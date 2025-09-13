"""
Enhanced Agent-to-Agent (A2A) Protocol Implementation
Implements full A2A specification including JSON-RPC 2.0, task management, streaming, and discovery
"""

import json
import uuid
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, Response, stream_with_context
import requests
from datetime import datetime
import threading
import queue

class TaskState(Enum):
    """Task lifecycle states as per A2A specification"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PartType(Enum):
    """Message part types as per A2A specification"""
    TEXT = "text"
    FILE = "file"
    DATA = "data"

@dataclass
class MessagePart:
    """Message part following A2A specification"""
    type: PartType
    content: Any
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class A2AMessage:
    """A2A message structure with multiple parts"""
    parts: List[MessagePart]
    timestamp: str
    message_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parts": [{"type": part.type.value, "content": part.content, "metadata": part.metadata} for part in self.parts],
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }

@dataclass
class TaskArtifact:
    """Tangible output generated during task execution"""
    artifact_id: str
    name: str
    type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

@dataclass
class A2ATask:
    """Task management following A2A specification"""
    task_id: str
    state: TaskState
    message: A2AMessage
    response: Optional[A2AMessage] = None
    artifacts: List[TaskArtifact] = None
    progress: float = 0.0
    error: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def update_state(self, new_state: TaskState, error: str = None):
        """Update task state with timestamp"""
        self.state = new_state
        self.updated_at = datetime.utcnow().isoformat()
        if error:
            self.error = error
    
    def add_artifact(self, artifact: TaskArtifact):
        """Add artifact to task"""
        self.artifacts.append(artifact)
        self.updated_at = datetime.utcnow().isoformat()

class JSONRPCRequest:
    """JSON-RPC 2.0 request implementation"""
    
    def __init__(self, method: str, params: Any = None, request_id: str = None):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params
        self.id = request_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id
        }
        if self.params is not None:
            result["params"] = self.params
        return result

class JSONRPCResponse:
    """JSON-RPC 2.0 response implementation"""
    
    def __init__(self, result: Any = None, error: Dict[str, Any] = None, request_id: str = None):
        self.jsonrpc = "2.0"
        self.id = request_id
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response

class A2AServer:
    """Enhanced A2A Server with full protocol support"""
    
    def __init__(self, agent_name: str, description: str, capabilities: List[str], 
                 model: str = "gemini-2.5-flash", version: str = "1.0"):
        self.agent_name = agent_name
        self.description = description
        self.capabilities = capabilities
        self.model = model
        self.version = version
        self.tasks: Dict[str, A2ATask] = {}
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Streaming support
        self.stream_queues: Dict[str, queue.Queue] = {}
        
    def setup_routes(self):
        """Setup Flask routes for A2A protocol endpoints"""
        
        @self.app.route('/.well-known/agent.json', methods=['GET'])
        def get_agent_card():
            """Agent discovery via well-known URI"""
            agent_card = {
                "name": self.agent_name,
                "description": self.description,
                "version": self.version,
                "capabilities": self.capabilities,
                "model": self.model,
                "authentication": {
                    "type": "none",
                    "required": False
                },
                "service_endpoint": f"http://localhost:{request.environ.get('SERVER_PORT', 8080)}",
                "protocols": ["a2a", "json-rpc-2.0"],
                "endpoints": {
                    "rpc": "/rpc",
                    "message/send": "/message/send", 
                    "message/stream": "/message/stream",
                    "tasks/get": "/tasks",
                    "tasks/create": "/tasks",
                    "tasks/status": "/tasks/{task_id}",
                    "artifacts/get": "/artifacts/{artifact_id}",
                    "health": "/health"
                },
                "input_format": ["text", "json"],
                "output_format": ["text", "json"],
                "streaming_support": True,
                "data_source": "MCP Server"
            }
            return jsonify(agent_card)
        
        @self.app.route('/rpc', methods=['POST'])
        def handle_rpc():
            """Main JSON-RPC 2.0 endpoint"""
            try:
                data = request.get_json()
                if not data or data.get("jsonrpc") != "2.0":
                    return jsonify(JSONRPCResponse(
                        error={"code": -32600, "message": "Invalid Request"},
                        request_id=data.get("id") if data else None
                    ).to_dict()), 400
                
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")
                
                if method == "message.send":
                    return self._handle_message_send(params, request_id)
                elif method == "tasks.get":
                    return self._handle_tasks_get(params, request_id)
                elif method == "tasks.create":
                    return self._handle_tasks_create(params, request_id)
                elif method == "artifacts.get":
                    return self._handle_artifacts_get(params, request_id)
                else:
                    return jsonify(JSONRPCResponse(
                        error={"code": -32601, "message": "Method not found"},
                        request_id=request_id
                    ).to_dict()), 404
                    
            except Exception as e:
                return jsonify(JSONRPCResponse(
                    error={"code": -32603, "message": f"Internal error: {str(e)}"},
                    request_id=data.get("id") if data else None
                ).to_dict()), 500
        
        @self.app.route('/message/send', methods=['POST'])
        def message_send():
            """Direct message sending endpoint"""
            data = request.get_json()
            return self._handle_message_send(data, str(uuid.uuid4()))
        
        @self.app.route('/message/stream', methods=['POST'])
        def message_stream():
            """Streaming message endpoint with SSE"""
            data = request.get_json()
            task_id = str(uuid.uuid4())
            
            def generate():
                try:
                    # Create task for streaming
                    message = A2AMessage(
                        parts=[MessagePart(PartType.TEXT, data.get("message", ""))],
                        timestamp=datetime.utcnow().isoformat(),
                        message_id=str(uuid.uuid4())
                    )
                    
                    task = A2ATask(
                        task_id=task_id,
                        state=TaskState.SUBMITTED,
                        message=message
                    )
                    
                    self.tasks[task_id] = task
                    
                    # Start processing and yield updates
                    yield f"data: {json.dumps({'type': 'task_created', 'task_id': task_id})}\n\n"
                    
                    # Update to working state
                    task.update_state(TaskState.WORKING)
                    yield f"data: {json.dumps({'type': 'state_change', 'task_id': task_id, 'state': 'working'})}\n\n"
                    
                    # Process message (this would call your actual agent logic)
                    result = self._process_message(data.get("message", ""))
                    
                    # Create response
                    response_message = A2AMessage(
                        parts=[MessagePart(PartType.TEXT, result)],
                        timestamp=datetime.utcnow().isoformat(),
                        message_id=str(uuid.uuid4())
                    )
                    
                    task.response = response_message
                    task.update_state(TaskState.COMPLETED)
                    task.progress = 1.0
                    
                    yield f"data: {json.dumps({'type': 'progress', 'task_id': task_id, 'progress': 1.0})}\n\n"
                    yield f"data: {json.dumps({'type': 'completed', 'task_id': task_id, 'result': result})}\n\n"
                    
                except Exception as e:
                    task.update_state(TaskState.FAILED, str(e))
                    yield f"data: {json.dumps({'type': 'error', 'task_id': task_id, 'error': str(e)})}\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
        @self.app.route('/tasks', methods=['GET'])
        def get_tasks():
            """Get all tasks"""
            return jsonify({
                "tasks": [
                    {
                        "task_id": task_id,
                        "state": task.state.value,
                        "progress": task.progress,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at
                    }
                    for task_id, task in self.tasks.items()
                ]
            })
        
        @self.app.route('/tasks/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            """Get specific task status"""
            if task_id not in self.tasks:
                return jsonify({"error": "Task not found"}), 404
            
            task = self.tasks[task_id]
            return jsonify({
                "task_id": task_id,
                "state": task.state.value,
                "progress": task.progress,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "message": task.message.to_dict(),
                "response": task.response.to_dict() if task.response else None,
                "artifacts": [asdict(artifact) for artifact in task.artifacts],
                "error": task.error
            })
        
        @self.app.route('/artifacts/<artifact_id>', methods=['GET'])
        def get_artifact(artifact_id):
            """Get specific artifact"""
            for task in self.tasks.values():
                for artifact in task.artifacts:
                    if artifact.artifact_id == artifact_id:
                        return jsonify(asdict(artifact))
            return jsonify({"error": "Artifact not found"}), 404
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "agent": self.agent_name,
                "version": self.version,
                "capabilities": self.capabilities,
                "active_tasks": len([t for t in self.tasks.values() if t.state == TaskState.WORKING])
            })
        
        # Legacy endpoints for backward compatibility
        @self.app.route('/agent-card', methods=['GET'])
        def legacy_agent_card():
            """Legacy agent card endpoint"""
            return get_agent_card()
        
        @self.app.route('/chat', methods=['POST'])
        def legacy_chat():
            """Legacy chat endpoint"""
            data = request.get_json()
            return self._handle_message_send(data, str(uuid.uuid4()))
    
    def _handle_message_send(self, params: Dict[str, Any], request_id: str):
        """Handle message.send JSON-RPC method"""
        try:
            message_content = params.get("message", "")
            
            # Create A2A message
            message = A2AMessage(
                parts=[MessagePart(PartType.TEXT, message_content)],
                timestamp=datetime.utcnow().isoformat(),
                message_id=str(uuid.uuid4())
            )
            
            # Create task
            task_id = str(uuid.uuid4())
            task = A2ATask(
                task_id=task_id,
                state=TaskState.SUBMITTED,
                message=message
            )
            
            self.tasks[task_id] = task
            
            # Process message
            task.update_state(TaskState.WORKING)
            result = self._process_message(message_content)
            
            # Create response
            response_message = A2AMessage(
                parts=[MessagePart(PartType.TEXT, result)],
                timestamp=datetime.utcnow().isoformat(),
                message_id=str(uuid.uuid4())
            )
            
            task.response = response_message
            task.update_state(TaskState.COMPLETED)
            task.progress = 1.0
            
            return jsonify(JSONRPCResponse(
                result={
                    "task_id": task_id,
                    "response": result,
                    "agent": self.agent_name,
                    "status": "success"
                },
                request_id=request_id
            ).to_dict())
            
        except Exception as e:
            return jsonify(JSONRPCResponse(
                error={"code": -32603, "message": f"Processing error: {str(e)}"},
                request_id=request_id
            ).to_dict()), 500
    
    def _handle_tasks_get(self, params: Dict[str, Any], request_id: str):
        """Handle tasks.get JSON-RPC method"""
        task_id = params.get("task_id")
        
        if task_id:
            if task_id not in self.tasks:
                return jsonify(JSONRPCResponse(
                    error={"code": -32602, "message": "Task not found"},
                    request_id=request_id
                ).to_dict()), 404
            
            task = self.tasks[task_id]
            return jsonify(JSONRPCResponse(
                result={
                    "task_id": task_id,
                    "state": task.state.value,
                    "progress": task.progress,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "message": task.message.to_dict(),
                    "response": task.response.to_dict() if task.response else None,
                    "artifacts": [asdict(artifact) for artifact in task.artifacts]
                },
                request_id=request_id
            ).to_dict())
        else:
            return jsonify(JSONRPCResponse(
                result={
                    "tasks": [
                        {
                            "task_id": tid,
                            "state": task.state.value,
                            "progress": task.progress,
                            "created_at": task.created_at,
                            "updated_at": task.updated_at
                        }
                        for tid, task in self.tasks.items()
                    ]
                },
                request_id=request_id
            ).to_dict())
    
    def _handle_tasks_create(self, params: Dict[str, Any], request_id: str):
        """Handle tasks.create JSON-RPC method"""
        message_content = params.get("message", "")
        
        message = A2AMessage(
            parts=[MessagePart(PartType.TEXT, message_content)],
            timestamp=datetime.utcnow().isoformat(),
            message_id=str(uuid.uuid4())
        )
        
        task_id = str(uuid.uuid4())
        task = A2ATask(
            task_id=task_id,
            state=TaskState.SUBMITTED,
            message=message
        )
        
        self.tasks[task_id] = task
        
        return jsonify(JSONRPCResponse(
            result={"task_id": task_id, "state": "submitted"},
            request_id=request_id
        ).to_dict())
    
    def _handle_artifacts_get(self, params: Dict[str, Any], request_id: str):
        """Handle artifacts.get JSON-RPC method"""
        artifact_id = params.get("artifact_id")
        
        for task in self.tasks.values():
            for artifact in task.artifacts:
                if artifact.artifact_id == artifact_id:
                    return jsonify(JSONRPCResponse(
                        result=asdict(artifact),
                        request_id=request_id
                    ).to_dict())
        
        return jsonify(JSONRPCResponse(
            error={"code": -32602, "message": "Artifact not found"},
            request_id=request_id
        ).to_dict()), 404
    
    def _process_message(self, message: str) -> str:
        """Override this method in subclasses to implement actual message processing"""
        return f"Processed: {message}"
    
    def run_server(self, host='localhost', port=8080, debug=False):
        """Start the A2A server"""
        print(f"🚀 Starting A2A Server '{self.agent_name}' on http://{host}:{port}")
        print(f"📋 Agent Card: http://{host}:{port}/.well-known/agent.json")
        print(f"🔌 JSON-RPC Endpoint: http://{host}:{port}/rpc")
        print(f"💬 Message Endpoint: http://{host}:{port}/message/send")
        print(f"📡 Streaming Endpoint: http://{host}:{port}/message/stream")
        
        self.app.run(host=host, port=port, debug=debug)

class A2AClient:
    """Enhanced A2A Client with full protocol support"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def discover_agent(self) -> Dict[str, Any]:
        """Discover agent capabilities via well-known URI"""
        try:
            response = requests.get(f"{self.base_url}/.well-known/agent.json", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            # Fallback to legacy endpoint
            try:
                response = requests.get(f"{self.base_url}/agent-card", timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass
        
        return {"name": "unknown", "status": "unavailable"}
    
    def send_rpc_request(self, method: str, params: Any = None) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 request"""
        rpc_request = JSONRPCRequest(method, params)
        
        try:
            response = requests.post(
                f"{self.base_url}/rpc",
                json=rpc_request.to_dict(),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": response.status_code, "message": response.text},
                    "id": rpc_request.id
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": rpc_request.id
            }
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send message using message.send method"""
        return self.send_rpc_request("message.send", {"message": message})
    
    def create_task(self, message: str) -> Dict[str, Any]:
        """Create task using tasks.create method"""
        return self.send_rpc_request("tasks.create", {"message": message})
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self.send_rpc_request("tasks.get", {"task_id": task_id})
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks"""
        return self.send_rpc_request("tasks.get")
    
    def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """Get artifact"""
        return self.send_rpc_request("artifacts.get", {"artifact_id": artifact_id})
    
    def stream_message(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream message with SSE support"""
        try:
            response = requests.post(
                f"{self.base_url}/message/stream",
                json={"message": message},
                headers={"Accept": "text/event-stream"},
                stream=True,
                timeout=60
            )
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield {"type": "error", "error": str(e)}
