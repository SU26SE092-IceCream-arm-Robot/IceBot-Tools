import re
import uuid
from codeintel.file_hashing import generate_file_id

# Regex for declarations (class, interface, enum, record, struct)
RE_DECLARATION = re.compile(
    r'\b(class|interface|enum|record|struct)\s+(\w+)(?:\s*:\s*([\w\.\s,<>]+))?',
    re.MULTILINE
)

# Regex for methods inside classes
RE_METHOD_DECL = re.compile(
    r'\b(public|internal)\s+(?:async\s+)?(?:Task\s*<\s*([^>]+)\s*>\s*|Task\s+|void\s+|([\w\.\?<>\[\]]+)\s+)'
    r'(\w+)\s*\(([^)]*?)\)',
    re.MULTILINE | re.DOTALL
)

# Regex for DI Registrations (e.g. services.AddScoped<IOrderStore, OrderStore>())
RE_DI_REGISTRATION = re.compile(
    r'\.Add(Scoped|Transient|Singleton)\s*<\s*([^,>\s]+)\s*(?:,\s*([^>\s]+)\s*)?>',
    re.MULTILINE
)

def get_line_number(content: str, char_index: int) -> int:
    """Returns the 1-indexed line number for a character index."""
    return content.count('\n', 0, char_index) + 1

def find_matching_brace(content: str, start_index: int) -> int:
    """Finds the character index of the matching closing brace '}'."""
    brace_index = content.find('{', start_index)
    if brace_index == -1:
        return -1
        
    nesting = 1
    i = brace_index + 1
    n = len(content)
    while i < n:
        c = content[i]
        if c == '{':
            nesting += 1
        elif c == '}':
            nesting -= 1
            if nesting == 0:
                return i
        i += 1
    return -1

def get_attributes_before(content: str, index: int) -> list:
    """Collects attributes (e.g., [Route(...)]) decorating an element starting at index."""
    sub = content[:index]
    lines = sub.splitlines()
    if not lines:
        return []
        
    collected = []
    for line in reversed(lines):
        line_strip = line.split('//')[0].strip()
        if not line_strip:
            continue
            
        # Matches one or more attributes on a single line, e.g. [HttpPost] [AllowAnonymous]
        matches = list(re.finditer(r'^(\s*\[[A-Za-z]+(?:\(.*?\))?\])+$', line_strip))
        if matches:
            for m in re.finditer(r'\[([A-Za-z]+)(?:\((.*?)\))?\]', line_strip):
                collected.append((m.group(1), m.group(2) if m.group(2) else ""))
        else:
            break
            
    collected.reverse()
    return collected

def extract_policy(args: str) -> str or None:
    """Extracts policy name from Authorize attribute args (e.g. Policy = "orders.view")."""
    match = re.search(r'(?:Policy\s*=\s*)?"([^"]+)"', args)
    if match:
        return match.group(1)
    return args.strip('" ') if args else None

def extract_api_version(args: str) -> str or None:
    """Extracts api version string (e.g. "1.0")."""
    match = re.search(r'"([^"]+)"', args)
    if match:
        return match.group(1)
    return args.strip('" ') if args else None

def compose_route(class_route: str, method_route: str) -> str:
    """Composes a class-level route with a method-level route template."""
    class_route = class_route.strip('"\' ')
    method_route = method_route.strip('"\' ')
    
    parts = []
    if class_route:
        parts.append(class_route.strip('/'))
    if method_route:
        parts.append(method_route.strip('/'))
        
    return "/".join(parts)

def determine_auth(class_attrs: list, method_attrs: list) -> tuple:
    """Determines auth_type and policy from class and method attributes.
    Returns (auth_type, policy)."""
    # 1. Check method level
    method_allow_anon = any(name == 'AllowAnonymous' for name, _ in method_attrs)
    if method_allow_anon:
        return 'anonymous', None
        
    method_auth = [args for name, args in method_attrs if name == 'Authorize']
    if method_auth:
        for args in method_auth:
            policy = extract_policy(args)
            if policy:
                return 'policy', policy
        return 'authenticated', None
        
    # 2. Check class level
    class_allow_anon = any(name == 'AllowAnonymous' for name, _ in class_attrs)
    if class_allow_anon:
        return 'anonymous', None
        
    class_auth = [args for name, args in class_attrs if name == 'Authorize']
    if class_auth:
        for args in class_auth:
            policy = extract_policy(args)
            if policy:
                return 'policy', policy
        return 'authenticated', None
        
    return 'unknown', None

def parse_base_types(base_str: str) -> list:
    """Parses base types/interfaces list, handling C# generic types correctly."""
    if not base_str:
        return []
    bases = []
    parts = []
    current_part = []
    nesting = 0
    for char in base_str:
        if char == '<':
            nesting += 1
        elif char == '>':
            nesting -= 1
            
        if char == ',' and nesting == 0:
            parts.append("".join(current_part).strip())
            current_part = []
        else:
            current_part.append(char)
    if current_part:
        parts.append("".join(current_part).strip())
        
    for p in parts:
        name = p.split('<')[0].strip()  # base interface/class name
        if name:
            bases.append(name)
    return bases

def extract_first_param_type(params_str: str) -> str or None:
    """Gets the C# type of the first method parameter."""
    if not params_str:
        return None
    parts = params_str.split(',')
    first_param = parts[0].strip()
    first_param = re.sub(r'\[[^\]]+\]', '', first_param).strip()  # remove attributes
    words = first_param.split()
    if len(words) >= 2:
        return words[-2]
    return None

def scan_constructors(class_name: str, content: str, class_start: int, class_end: int) -> list:
    """Scans for constructors inside the class and extracts injected parameter types."""
    pattern = rf'\bpublic\s+{class_name}\s*\(([^)]*?)\)'
    injections = []
    class_content = content[class_start:class_end]
    for m in re.finditer(pattern, class_content):
        params_str = m.group(1)
        line_start = get_line_number(content, class_start + m.start())
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue
            parts = param.split()
            if len(parts) >= 2:
                param_type = parts[-2]
                param_name = parts[-1]
                injections.append({
                    "type": param_type.strip('?'), # strip nullable marker
                    "name": param_name,
                    "line": line_start
                })
    return injections

def scan_handler_fields(content: str, class_start: int, class_end: int) -> dict:
    """Maps controller handler fields to their concrete handler type."""
    class_content = content[class_start:class_end]
    fields = {}
    field_pattern = re.compile(
        r'\b(?:private|protected|internal)\s+readonly\s+([\w\.]+Handler)\s+(_\w+)\s*;',
        re.MULTILINE
    )
    for m in field_pattern.finditer(class_content):
        handler_type = m.group(1).split('.')[-1]
        field_name = m.group(2)
        fields[field_name] = handler_type
    return fields

def extract_method_body(content: str, method_decl_end: int) -> str:
    """Returns method body text for a method declaration when a block body exists."""
    body_end = find_matching_brace(content, method_decl_end)
    if body_end == -1:
        return ""
    body_start = content.find('{', method_decl_end)
    if body_start == -1 or body_start >= body_end:
        return ""
    return content[body_start:body_end + 1]

def resolve_called_handler(method_body: str, handler_fields: dict) -> str or None:
    """Finds the concrete handler called by a controller action body."""
    if not method_body or not handler_fields:
        return None

    # Common CQRS style: await _placeOrderHandler.HandleAsync(...)
    for m in re.finditer(r'\b(_\w+)\s*\.\s*Handle(?:Async)?\s*\(', method_body):
        field_name = m.group(1)
        handler_name = handler_fields.get(field_name)
        if handler_name:
            return handler_name

    return None

def scan_csharp_file(file_content: str, file_id: str, repo_key: str, project_key: str, bounded_context: str or None) -> dict:
    """Scans C# source code and extracts symbols, endpoints, graphql_fields, handlers, stores and relationships."""
    namespaces = []
    for m in re.finditer(r'\bnamespace\s+([\w\.]+)(?:\s*;|\s*\{)', file_content):
        namespaces.append((m.group(1), m.start()))
        
    def find_containing_ns(index: int) -> str:
        applicable = [ns for ns in namespaces if ns[1] <= index]
        if not applicable:
            return ""
        applicable.sort(key=lambda ns: ns[1], reverse=True)
        return applicable[0][0]

    classes_info = []
    for m in re.finditer(RE_DECLARATION, file_content):
        kind = m.group(1)
        name = m.group(2)
        base_types_str = m.group(3) if m.group(3) else ""
        
        start_idx = m.start()
        end_idx = find_matching_brace(file_content, start_idx)
        if end_idx == -1:
            end_idx = len(file_content)
            
        classes_info.append({
            "name": name,
            "kind": kind,
            "base_types": base_types_str,
            "start": start_idx,
            "end": end_idx,
            "line_start": get_line_number(file_content, start_idx),
            "line_end": get_line_number(file_content, end_idx)
        })

    def find_containing_class(index: int) -> dict or None:
        containers = [c for c in classes_info if c['start'] <= index <= c['end']]
        if not containers:
            return None
        containers.sort(key=lambda c: c['end'] - c['start'])
        return containers[0]

    # Data collections
    symbols = []
    endpoints = []
    graphql_fields = []
    handlers = []
    stores_raw = []
    relationships = []
    handler_fields_by_class = {}

    # 1. Process class declarations
    for c in classes_info:
        ns = find_containing_ns(c["start"])
        parent_class = find_containing_class(c["start"] - 1)
        
        full_name = f"{ns}.{c['name']}" if ns else c['name']
        if parent_class:
            # Handle nested class full name
            parent_ns = find_containing_ns(parent_class["start"])
            parent_full_name = f"{parent_ns}.{parent_class['name']}" if parent_ns else parent_class['name']
            full_name = f"{parent_full_name}.{c['name']}"
            
        c_line_start = file_content.rfind('\n', 0, c["start"]) + 1
        class_attrs = get_attributes_before(file_content, c_line_start)
        
        # Add Class Symbol
        symbols.append({
            "id": str(uuid.uuid4()),
            "file_id": file_id,
            "repository_key": repo_key,
            "project_key": project_key,
            "bounded_context": bounded_context,
            "language": "csharp",
            "kind": c["kind"],
            "name": c["name"],
            "full_name": full_name,
            "namespace": ns or None,
            "containing_type": parent_class["name"] if parent_class else None,
            "signature": f"public {c['kind']} {c['name']}",
            "line_start": c["line_start"],
            "line_end": c["line_end"]
        })
        
        # Register base implements relationships
        base_types = parse_base_types(c["base_types"])
        for base in base_types:
            relationships.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "from_kind": c["kind"],
                "from_name": c["name"],
                "from_context": bounded_context,
                "to_kind": "interface" if base.startswith("I") else "class",
                "to_name": base,
                "to_context": bounded_context,
                "relation_type": "implements",
                "evidence_file_id": file_id,
                "line_start": c["line_start"]
            })
            
        # Is Store?
        if c["name"].endswith("Store"):
            if c["kind"] == "interface" and c["name"].startswith("I"):
                stores_raw.append({
                    "type": "interface",
                    "name": c["name"],
                    "file_id": file_id,
                    "bounded_context": bounded_context
                })
            elif c["kind"] == "class":
                stores_raw.append({
                    "type": "implementation",
                    "name": c["name"],
                    "file_id": file_id,
                    "bounded_context": bounded_context,
                    "base_types": base_types
                })
                
        # Is Handler?
        if c["name"].endswith("CommandHandler") or c["name"].endswith("QueryHandler"):
            handler_type = "command" if c["name"].endswith("CommandHandler") else "query"
            handlers.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "project_key": project_key,
                "handler_name": c["name"],
                "handler_type": handler_type,
                "request_name": None, # parsed inside methods
                "result_name": None,  # parsed inside methods
                "bounded_context": bounded_context,
                "file_id": file_id,
                "line_start": c["line_start"]
            })
            
        # Scan constructor parameter injections
        if c["name"].endswith("Controller"):
            handler_fields_by_class[c["name"]] = scan_handler_fields(file_content, c["start"], c["end"])

        injections = scan_constructors(c["name"], file_content, c["start"], c["end"])
        for inj in injections:
            # Relationship: injects
            relationships.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "from_kind": c["kind"],
                "from_name": c["name"],
                "from_context": bounded_context,
                "to_kind": "interface" if inj["type"].startswith("I") else "class",
                "to_name": inj["type"],
                "to_context": bounded_context,
                "relation_type": "injects",
                "evidence_file_id": file_id,
                "line_start": inj["line"]
            })
            
            # Handler-specific relationship mapping
            if c["name"].endswith("CommandHandler") or c["name"].endswith("QueryHandler"):
                if inj["type"].endswith("Store"):
                    relationships.append({
                        "id": str(uuid.uuid4()),
                        "repository_key": repo_key,
                        "from_kind": "handler",
                        "from_name": c["name"],
                        "from_context": bounded_context,
                        "to_kind": "store",
                        "to_name": inj["type"],
                        "to_context": bounded_context,
                        "relation_type": "uses_store",
                        "evidence_file_id": file_id,
                        "line_start": inj["line"]
                    })
            # Controller calls handler mapping
            elif c["name"].endswith("Controller"):
                if inj["type"].endswith("Handler"):
                    relationships.append({
                        "id": str(uuid.uuid4()),
                        "repository_key": repo_key,
                        "from_kind": "controller",
                        "from_name": c["name"],
                        "from_context": bounded_context,
                        "to_kind": "handler",
                        "to_name": inj["type"],
                        "to_context": bounded_context,
                        "relation_type": "calls_handler",
                        "evidence_file_id": file_id,
                        "line_start": inj["line"]
                    })

    # 2. Process method declarations
    for m in re.finditer(RE_METHOD_DECL, file_content):
        start_idx = m.start()
        line_start = get_line_number(file_content, start_idx)
        
        containing_class = find_containing_class(start_idx)
        if not containing_class:
            continue
            
        ns = find_containing_ns(containing_class["start"])
        class_full_name = f"{ns}.{containing_class['name']}" if ns else containing_class['name']
        
        access = m.group(1)
        task_inner = m.group(2)
        other_ret = m.group(3)
        method_name = m.group(4)
        params_str = m.group(5)
        
        # Determine return type name
        return_type = task_inner if task_inner else (other_ret if other_ret else "Task")
        
        # Skip constructors (safety check)
        if method_name == containing_class["name"]:
            continue
            
        m_line_start = file_content.rfind('\n', 0, start_idx) + 1
        method_attrs = get_attributes_before(file_content, m_line_start)
        
        cc_line_start = file_content.rfind('\n', 0, containing_class["start"]) + 1
        class_attrs = get_attributes_before(file_content, cc_line_start)
        
        # Cleaned signature
        sig_text = file_content[m.start():m.end()]
        signature = " ".join(sig_text.split())
        
        # Add Method Symbol
        symbols.append({
            "id": str(uuid.uuid4()),
            "file_id": file_id,
            "repository_key": repo_key,
            "project_key": project_key,
            "bounded_context": bounded_context,
            "language": "csharp",
            "kind": "method",
            "name": method_name,
            "full_name": f"{class_full_name}.{method_name}",
            "namespace": ns or None,
            "containing_type": containing_class["name"],
            "signature": signature,
            "line_start": line_start,
            "line_end": line_start # estimate same line
        })
        
        # If class is a Controller
        is_controller = containing_class["name"].endswith("Controller") or any(name == 'ApiController' for name, _ in class_attrs)
        if is_controller:
            # Check for HTTP verb decorators
            http_verb = None
            route_template = ""
            for name, args in method_attrs:
                if name in ('HttpGet', 'HttpPost', 'HttpPut', 'HttpDelete', 'HttpPatch'):
                    http_verb = name[4:].upper()  # GET, POST, etc.
                    route_template = args.strip('"\' ')
                    break
                    
            if http_verb:
                # Composed Class-level route
                class_route = ""
                for name, args in class_attrs:
                    if name == 'Route':
                        class_route = args.strip('"\' ')
                        break
                        
                composed = compose_route(class_route, route_template)
                
                # Auth details
                auth_type, policy = determine_auth(class_attrs, method_attrs)
                
                # API Version
                api_version = None
                for name, args in class_attrs:
                    if name == 'ApiVersion':
                        api_version = extract_api_version(args)
                        break
                        
                method_body = extract_method_body(file_content, m.end())
                handler_name = resolve_called_handler(
                    method_body,
                    handler_fields_by_class.get(containing_class["name"], {})
                )
                
                endpoints.append({
                    "id": str(uuid.uuid4()),
                    "repository_key": repo_key,
                    "project_key": project_key,
                    "bounded_context": bounded_context,
                    "http_method": http_verb,
                    "route": composed,
                    "api_version": api_version,
                    "controller": containing_class["name"],
                    "action": method_name,
                    "auth_type": auth_type,
                    "policy": policy,
                    "handler_name": handler_name,
                    "file_id": file_id,
                    "line_start": line_start
                })
                
                # Relationship: maps_route_to_action
                relationships.append({
                    "id": str(uuid.uuid4()),
                    "repository_key": repo_key,
                    "from_kind": "route",
                    "from_name": f"{http_verb} {composed}",
                    "from_context": bounded_context,
                    "to_kind": "method",
                    "to_name": f"{containing_class['name']}.{method_name}",
                    "to_context": bounded_context,
                    "relation_type": "maps_route_to_action",
                    "evidence_file_id": file_id,
                    "line_start": line_start
                })

                if handler_name:
                    relationships.append({
                        "id": str(uuid.uuid4()),
                        "repository_key": repo_key,
                        "from_kind": "route",
                        "from_name": f"{http_verb} {composed}",
                        "from_context": bounded_context,
                        "to_kind": "handler",
                        "to_name": handler_name,
                        "to_context": bounded_context,
                        "relation_type": "maps_endpoint_to_handler",
                        "evidence_file_id": file_id,
                        "line_start": line_start
                    })
                
        # If class is GraphQL Query/Mutation Extender
        extend_type = None
        for name, args in class_attrs:
            if name == 'ExtendObjectType':
                extend_type = args.strip('"\' ').lower() # query or mutation
                break
                
        if extend_type in ('query', 'mutation'):
            # Auth details
            auth_type, policy = determine_auth(class_attrs, method_attrs)
            
            # Find [Service] parameter injection
            handler_name = None
            service_match = re.search(r'\[Service\]\s+(\w+)', params_str)
            if service_match:
                handler_name = service_match.group(1)
                
            graphql_fields.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "bounded_context": bounded_context,
                "field_type": extend_type,
                "field_name": method_name,
                "resolver": f"{containing_class['name']}.{method_name}",
                "auth_type": auth_type,
                "policy": policy,
                "handler_name": handler_name,
                "file_id": file_id,
                "line_start": line_start
            })
            
            # Relationship: maps_graphql_to_handler
            if handler_name:
                relationships.append({
                    "id": str(uuid.uuid4()),
                    "repository_key": repo_key,
                    "from_kind": "graphql",
                    "from_name": f"{extend_type}.{method_name}",
                    "from_context": bounded_context,
                    "to_kind": "handler",
                    "to_name": handler_name,
                    "to_context": bounded_context,
                    "relation_type": "maps_graphql_to_handler",
                    "evidence_file_id": file_id,
                    "line_start": line_start
                })
                
        # If class is a Handler
        is_handler = containing_class["name"].endswith("CommandHandler") or containing_class["name"].endswith("QueryHandler")
        if is_handler and method_name in ('Handle', 'HandleAsync'):
            # Extract request and result type
            req_type = extract_first_param_type(params_str)
            
            # Find and update handler info
            for h in handlers:
                if h["handler_name"] == containing_class["name"]:
                    h["request_name"] = req_type
                    h["result_name"] = return_type
                    break

    # 3. Process DI Registrations
    for m in re.finditer(RE_DI_REGISTRATION, file_content):
        line_start = get_line_number(file_content, m.start())
        di_kind = m.group(1)
        interface_or_service = m.group(2)
        implementation = m.group(3) # could be None
        
        # Add registers_di relationship for interface/service
        relationships.append({
            "id": str(uuid.uuid4()),
            "repository_key": repo_key,
            "from_kind": "file",
            "from_name": file_id, # link to current file
            "from_context": bounded_context,
            "to_kind": "interface" if interface_or_service.startswith("I") else "class",
            "to_name": interface_or_service,
            "to_context": bounded_context,
            "relation_type": "registers_di",
            "evidence_file_id": file_id,
            "line_start": line_start
        })
        
        # If implementation exists, register di for it and link implements relationship
        if implementation:
            relationships.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "from_kind": "file",
                "from_name": file_id,
                "from_context": bounded_context,
                "to_kind": "class",
                "to_name": implementation,
                "to_context": bounded_context,
                "relation_type": "registers_di",
                "evidence_file_id": file_id,
                "line_start": line_start
            })
            
            # Also registers implements
            relationships.append({
                "id": str(uuid.uuid4()),
                "repository_key": repo_key,
                "from_kind": "class",
                "from_name": implementation,
                "from_context": bounded_context,
                "to_kind": "interface",
                "to_name": interface_or_service,
                "to_context": bounded_context,
                "relation_type": "implements",
                "evidence_file_id": file_id,
                "line_start": line_start
            })

    return {
        "symbols": symbols,
        "endpoints": endpoints,
        "graphql_fields": graphql_fields,
        "handlers": handlers,
        "stores_raw": stores_raw,
        "relationships": relationships
    }
