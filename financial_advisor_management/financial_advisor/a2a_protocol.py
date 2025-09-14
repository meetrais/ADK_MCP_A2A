"""
Enhanced Agent-to-Agent (A2A) Protocol Implementation
Proper JSON-RPC 2.0 Implementation following the official specification
Incorporating expert improvements for full compliance
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

# JSON-RPC 2.0 Error Codes (from specification)
class JSONRPCErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # Server error range: -32000 to -32099

@dataclass
class JSONRPCError:
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

@dataclass
class JSONRPCRequest:
    method: str
    params: Optional[Union[Dict, list]] = None
    id: Optional[Union[str, int]] = None
    jsonrpc: str = "2.0"
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id
        }
        if self.params is not None:
            result["params"] = self.params
        return result
    
    def is_notification(self) -> bool:
        """Check if this is a notification (no response expected)"""
        return self.id is None

@dataclass
class JSONRPCResponse:
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        
        if self.error is not None:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
            
        return response
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCResponse':
        """Create response from dictionary with validation"""
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        
        error_data = data.get("error")
        error = None
        if error_data:
            error = JSONRPCError(
                code=error_data["code"],
                message=error_data["message"],
                data=error_data.get("data")
            )
        
        return cls(
            jsonrpc=data["jsonrpc"],
            id=data.get("id"),
            result=data.get("result"),
            error=error
        )
    
    def is_error(self) -> bool:
        return self.error is not None

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
    priority: str = "normal"
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

class ImprovedJSONRPCServer:
    """Improved JSON-RPC 2.0 Server with full specification compliance"""
    
    def __init__(self):
        self.methods: Dict[str, callable] = {}
    
    def register_method(self, name: str, method: callable):
        """Register a method that can be called via JSON-RPC"""
        self.methods[name] = method
    
    def handle_request(self, request_data: Union[Dict, List]) -> Optional[Union[Dict, List]]:
        """
        Handle JSON-RPC 2.0 request with full specification compliance
        Supports both single requests and batch requests
        """
        
        # Handle batch requests (array of requests)
        if isinstance(request_data, list):
            if len(request_data) == 0:
                return self._error_response(None, JSONRPCErrorCode.INVALID_REQUEST, "Invalid Request", "Empty batch request")
            
            responses = []
            for single_request in request_data:
                response = self._handle_single_request(single_request)
                if response is not None:  # Don't include notification responses
                    responses.append(response)
            
            # Return responses or nothing if all were notifications
            return responses if responses else None
        
        # Handle single request
        return self._handle_single_request(request_data)
    
    def _handle_single_request(self, request_data: Any) -> Optional[Dict[str, Any]]:
        """Handle a single JSON-RPC request"""
        
        # Validate basic structure
        if not isinstance(request_data, dict):
            return self._error_response(None, JSONRPCErrorCode.INVALID_REQUEST, "Invalid Request", "Request must be an object")
        
        # Check JSON-RPC version
        if request_data.get("jsonrpc") != "2.0":
            return self._error_response(
                request_data.get("id"), 
                JSONRPCErrorCode.INVALID_REQUEST, 
                "Invalid Request", 
                "jsonrpc field must be '2.0'"
            )
        
        # Check method field
        method_name = request_data.get("method")
        if not isinstance(method_name, str):
            return self._error_response(
                request_data.get("id"), 
                JSONRPCErrorCode.INVALID_REQUEST, 
                "Invalid Request", 
                "method field must be a string"
            )
        
        # Check if method name starts with "rpc." (reserved)
        if method_name.startswith("rpc.") and method_name not in ["rpc.discover"]:
            return self._error_response(
                request_data.get("id"),
                JSONRPCErrorCode.METHOD_NOT_FOUND,
                "Method not found",
                f"Method names starting with 'rpc.' are reserved"
            )
        
        params = request_data.get("params")
        request_id = request_data.get("id")
        
        # Validate params if present
        if params is not None and not isinstance(params, (dict, list)):
            return self._error_response(
                request_id,
                JSONRPCErrorCode.INVALID_PARAMS,
                "Invalid params",
                "params must be an object or array"
            )
        
        # Check if it's a notification
        is_notification = "id" not in request_data  # Note: id can be null, but must be present
        
        # Check if method exists
        if method_name not in self.methods:
            if not is_notification:
                return self._error_response(
                    request_id, 
                    JSONRPCErrorCode.METHOD_NOT_FOUND, 
                    "Method not found", 
                    f"Method '{method_name}' not found"
                )
            return None
        
        # Call method with proper error handling
        try:
            method = self.methods[method_name]
            
            # Call with or without params
            if params is None:
                result = method()
            elif isinstance(params, list):
                # Positional parameters
                result = method(*params)
            elif isinstance(params, dict):
                # Named parameters
                result = method(**params)
            
            # Return result (or nothing for notifications)
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            
            return None
            
        except TypeError as e:
            # Parameter mismatch
            if not is_notification:
                return self._error_response(
                    request_id, 
                    JSONRPCErrorCode.INVALID_PARAMS, 
                    "Invalid params", 
                    f"Parameter mismatch: {str(e)}"
                )
            return None
        except Exception as e:
            # Internal error
            if not is_notification:
                return self._error_response(
                    request_id, 
                    JSONRPCErrorCode.INTERNAL_ERROR, 
                    "Internal error", 
                    f"Method execution failed: {str(e)}"
                )
            return None
    
    def _error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """Create properly formatted error response"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id
        }

class JSONRPCClient:
    """Proper JSON-RPC 2.0 Client with full validation"""
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def send_request(self, method: str, params: Any = None, 
                    request_id: Optional[Union[str, int]] = None) -> JSONRPCResponse:
        """Send JSON-RPC 2.0 request with proper validation"""
        
        # Create request
        request = JSONRPCRequest(method=method, params=params, id=request_id)
        
        try:
            # Send HTTP request
            http_response = self.session.post(
                f"{self.base_url}/rpc",
                json=request.to_dict(),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=self.timeout
            )
            
            # JSON-RPC 2.0 spec: Always return HTTP 200 for application-level errors
            if http_response.status_code != 200:
                return self._create_error_response(
                    request.id,
                    JSONRPCErrorCode.INTERNAL_ERROR,
                    f"HTTP {http_response.status_code}: {http_response.reason}",
                    {"http_status": http_response.status_code, "http_body": http_response.text}
                )
            
            # Validate Content-Type
            content_type = http_response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return self._create_error_response(
                    request.id,
                    JSONRPCErrorCode.INTERNAL_ERROR,
                    "Invalid content type",
                    {"content_type": content_type}
                )
            
            # Parse JSON response
            try:
                response_data = http_response.json()
            except json.JSONDecodeError as e:
                return self._create_error_response(
                    request.id,
                    JSONRPCErrorCode.PARSE_ERROR,
                    "Invalid JSON response",
                    {"parse_error": str(e)}
                )
            
            # Validate and create JSON-RPC response
            try:
                response = JSONRPCResponse.from_dict(response_data)
                
                # Validate ID matches (unless it's an error response to invalid request)
                if response.id != request.id and response_data.get("error", {}).get("code") != JSONRPCErrorCode.INVALID_REQUEST:
                    return self._create_error_response(
                        request.id,
                        JSONRPCErrorCode.INTERNAL_ERROR,
                        "Response ID mismatch",
                        {"expected_id": request.id, "received_id": response.id}
                    )
                
                return response
                
            except (ValueError, KeyError) as e:
                return self._create_error_response(
                    request.id,
                    JSONRPCErrorCode.INVALID_REQUEST,
                    "Invalid JSON-RPC response format",
                    {"validation_error": str(e)}
                )
                
        except requests.exceptions.Timeout:
            return self._create_error_response(
                request.id,
                JSONRPCErrorCode.INTERNAL_ERROR,
                "Request timeout",
                {"timeout": self.timeout}
            )
        except requests.exceptions.ConnectionError as e:
            return self._create_error_response(
                request.id,
                JSONRPCErrorCode.INTERNAL_ERROR,
                "Connection error",
                {"connection_error": str(e)}
            )
        except Exception as e:
            return self._create_error_response(
                request.id,
                JSONRPCErrorCode.INTERNAL_ERROR,
                "Unexpected error",
                {"exception": str(e), "type": type(e).__name__}
            )
    
    def send_notification(self, method: str, params: Any = None) -> bool:
        """Send notification (no response expected)"""
        request = JSONRPCRequest(method=method, params=params, id=None)
        
        try:
            http_response = self.session.post(
                f"{self.base_url}/rpc",
                json=request.to_dict(),
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            return http_response.status_code in [200, 204]
        except:
            return False
    
    def _create_error_response(self, request_id: Optional[Union[str, int]], 
                             code: int, message: str, data: Any = None) -> JSONRPCResponse:
        """Create properly formatted error response"""
        return JSONRPCResponse(
            id=request_id,
            error=JSONRPCError(code=code, message=message, data=data)
        )

class A2AServer:
    """Enhanced A2A Server with improved JSON-RPC 2.0 compliance"""
    
    def __init__(self, agent_name: str, description: str, capabilities: List[str], 
                 model: str = "gemini-2.5-flash", version: str = "1.0"):
        self.agent_name = agent_name
        self.description = description
        self.capabilities = capabilities
        self.model = model
        self.version = version
        self.tasks: Dict[str, A2ATask] = {}
        self.app = Flask(__name__)
        self.rpc_server = ImprovedJSONRPCServer()
        self.setup_routes()
        self.setup_rpc_methods()
        
        # Streaming support
        self.stream_queues: Dict[str, queue.Queue] = {}
        
    def setup_rpc_methods(self):
        """Setup JSON-RPC 2.0 methods with proper signatures and validation"""
        
        # Register built-in method for service discovery
        self.rpc_server.register_method("rpc.discover", self._rpc_discover)
        
        # Register A2A-specific methods
        self.rpc_server.register_method("message.send", self._rpc_message_send)
        self.rpc_server.register_method("tasks.get", self._rpc_tasks_get)
        self.rpc_server.register_method("tasks.create", self._rpc_tasks_create)
        self.rpc_server.register_method("tasks.cancel", self._rpc_tasks_cancel)
        self.rpc_server.register_method("artifacts.get", self._rpc_artifacts_get)
        
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
            """
            Main JSON-RPC 2.0 endpoint with full specification compliance
            Always returns HTTP 200 as per JSON-RPC 2.0 spec
            """
            try:
                # Parse JSON
                try:
                    data = request.get_json(force=True)  # Force parsing even with wrong content-type
                except Exception:
                    # Parse error - return HTTP 200 with JSON-RPC error
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": JSONRPCErrorCode.PARSE_ERROR,
                            "message": "Parse error",
                            "data": "Invalid JSON was received by the server"
                        },
                        "id": None
                    }), 200  # Note: HTTP 200, not 400
                
                # Handle request
                response = self.rpc_server.handle_request(data)
                
                if response is not None:
                    return jsonify(response), 200
                else:
                    # Notification - return HTTP 204 No Content
                    return "", 204
                    
            except Exception as e:
                # Unexpected server error
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": JSONRPCErrorCode.INTERNAL_ERROR,
                        "message": "Internal error",
                        "data": f"Unexpected server error: {str(e)}"
                    },
                    "id": None
                }), 200  # Still HTTP 200
        
        @self.app.route('/message/send', methods=['POST'])
        def message_send():
            """Direct message sending endpoint"""
            data = request.get_json()
            result = self._handle_message_send(data.get("message", ""))
            return jsonify(result)
        
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
                    yield f"data: {json.dumps({'type': 'task_created', 'task_id': task_id})}\\n\\n"
                    
                    # Update to working state
                    task.update_state(TaskState.WORKING)
                    yield f"data: {json.dumps({'type': 'state_change', 'task_id': task_id, 'state': 'working'})}\\n\\n"
                    
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
                    
                    yield f"data: {json.dumps({'type': 'progress', 'task_id': task_id, 'progress': 1.0})}\\n\\n"
                    yield f"data: {json.dumps({'type': 'completed', 'task_id': task_id, 'result': result})}\\n\\n"
                    
                except Exception as e:
                    if task_id in self.tasks:
                        self.tasks[task_id].update_state(TaskState.FAILED, str(e))
                    yield f"data: {json.dumps({'type': 'error', 'task_id': task_id, 'error': str(e)})}\\n\\n"
            
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
                        "priority": task.priority,
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
                "priority": task.priority,
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
            result = self._handle_message_send(data.get("message", ""))
            return jsonify(result)
    
    def _rpc_discover(self) -> Dict[str, Any]:
        """JSON-RPC method: rpc.discover - Service discovery"""
        return {
            "name": self.agent_name,
            "description": self.description,
            "methods": list(self.rpc_server.methods.keys()),
            "version": self.version,
            "protocol": "JSON-RPC 2.0",
            "capabilities": ["batch_requests", "notifications", "a2a_protocol"] + self.capabilities
        }
    
    def _rpc_message_send(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """JSON-RPC method: message.send with proper parameter validation"""
        if not isinstance(message, str):
            raise TypeError("message parameter must be a string")
        
        if context is not None and not isinstance(context, dict):
            raise TypeError("context parameter must be an object")
        
        # Process message
        result = self._handle_message_send(message)
        
        return {
            "response": result.get("response", ""),
            "agent": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": result.get("task_id")
        }
    
    def _rpc_tasks_get(self, task_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """JSON-RPC method: tasks.get with optional task_id parameter"""
        if task_id is not None:
            if not isinstance(task_id, str):
                raise TypeError("task_id parameter must be a string")
            
            if task_id not in self.tasks:
                raise ValueError(f"Task '{task_id}' not found")
            
            task = self.tasks[task_id]
            return {
                "task_id": task_id,
                "state": task.state.value,
                "progress": task.progress,
                "priority": task.priority,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "message": task.message.to_dict(),
                "response": task.response.to_dict() if task.response else None,
                "artifacts": [asdict(artifact) for artifact in task.artifacts]
            }
        else:
            return [
                {
                    "task_id": tid,
                    "state": task.state.value,
                    "progress": task.progress,
                    "priority": task.priority,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                }
                for tid, task in self.tasks.items()
            ]
    
    def _rpc_tasks_create(self, message: str, priority: str = "normal") -> Dict[str, Any]:
        """JSON-RPC method: tasks.create with parameter validation"""
        if not isinstance(message, str):
            raise TypeError("message parameter must be a string")
        
        if priority not in ["low", "normal", "high"]:
            raise ValueError("priority must be one of: low, normal, high")
        
        message_obj = A2AMessage(
            parts=[MessagePart(PartType.TEXT, message)],
            timestamp=datetime.utcnow().isoformat(),
            message_id=str(uuid.uuid4())
        )
        
        task_id = str(uuid.uuid4())
        task = A2ATask(
            task_id=task_id,
            state=TaskState.SUBMITTED,
            message=message_obj,
            priority=priority
        )
        
        self.tasks[task_id] = task
        
        return {
            "task_id": task_id,
            "state": "submitted",
            "priority": priority
        }
    
    def _rpc_tasks_cancel(self, task_id: str) -> Dict[str, Any]:
        """JSON-RPC method: tasks.cancel"""
        if not isinstance(task_id, str):
            raise TypeError("task_id parameter must be a string")
        
        if task_id not in self.tasks:
            raise ValueError(f"Task '{task_id}' not found")
        
        task = self.tasks[task_id]
        if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
            raise ValueError(f"Cannot cancel task in {task.state.value} state")
        
        task.update_state(TaskState.CANCELLED)
        
        return {"task_id": task_id, "state": "cancelled"}
    
    def _rpc_artifacts_get(self, artifact_id: str) -> Dict[str, Any]:
        """JSON-RPC method: artifacts.get"""
        if not isinstance(artifact_id, str):
            raise TypeError("artifact_id parameter must be a string")
        
        for task in self.tasks.values():
            for artifact in task.artifacts:
                if artifact.artifact_id == artifact_id:
                    return asdict(artifact)
        
        raise ValueError(f"Artifact '{artifact_id}' not found")
    
    def _handle_message_send(self, message_content: str) -> Dict[str, Any]:
        """Handle message sending with proper A2A protocol"""
        try:
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
            
            return {
                "task_id": task_id,
                "response": result,
                "agent": self.agent_name,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "agent": self.agent_name,
                "status": "error"
            }
    
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
    """Enhanced A2A Client with proper JSON-RPC 2.0 support"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.json_rpc_client = JSONRPCClient(base_url)
        
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
    
    def discover_service(self) -> JSONRPCResponse:
        """Discover service capabilities via JSON-RPC"""
        return self.json_rpc_client.send_request("rpc.discover")
    
    def send_rpc_request(self, method: str, params: Any = None) -> JSONRPCResponse:
        """Send JSON-RPC 2.0 request with proper validation"""
        return self.json_rpc_client.send_request(method, params)
    
    def send_message(self, message: str, context: Dict[str, Any] = None) -> JSONRPCResponse:
        """Send message using message.send method"""
        params = {"message": message}
        if context:
            params["context"] = context
        return self.send_rpc_request("message.send", params)
    
    def create_task(self, message: str, priority: str = "normal") -> JSONRPCResponse:
        """Create task using tasks.create method"""
        return self.send_rpc_request("tasks.create", {"message": message, "priority": priority})
    
    def get_task_status(self, task_id: str) -> JSONRPCResponse:
        """Get task status"""
        return self.send_rpc_request("tasks.get", {"task_id": task_id})
    
    def cancel_task(self, task_id: str) -> JSONRPCResponse:
        """Cancel task"""
        return self.send_rpc_request("tasks.cancel", {"task_id": task_id})
    
    def get_all_tasks(self) -> JSONRPCResponse:
        """Get all tasks"""
        return self.send_rpc_request("tasks.get")
    
    def get_artifact(self, artifact_id: str) -> JSONRPCResponse:
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
