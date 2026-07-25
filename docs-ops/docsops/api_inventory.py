from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from toolcore.workspace import WORKSPACE_ROOT


BACKEND_ROOT = WORKSPACE_ROOT / "IceBot-Backend"
CONTROLLERS_ROOT = BACKEND_ROOT / "src" / "WebAPI" / "Controllers"
GRAPHQL_ROOT = BACKEND_ROOT / "src" / "WebAPI" / "GraphQL"
PERMISSION_MATRIX = (
    BACKEND_ROOT
    / "src"
    / "Application"
    / "Identity"
    / "Roles"
    / "Queries"
    / "GetPermissionMatrixQueryHandler.cs"
)
AUTHORIZATION_POLICY_EXTENSIONS = (
    BACKEND_ROOT / "src" / "WebAPI" / "Authorization" / "AuthorizationPolicyExtensions.cs"
)

ROUTE_ATTRIBUTE_RE = re.compile(r'\[Route\("(?P<route>[^"]+)"\)\]')
HTTP_ATTRIBUTE_RE = re.compile(
    r'\[Http(?P<method>Get|Post|Put|Patch|Delete|Head|Options)(?:\("(?P<route>[^"]*)"\))?\]'
)
POLICY_RE = re.compile(r'\[Authorize\(Policy\s*=\s*"(?P<policy>[^"]+)"\)\]')
CLASS_RE = re.compile(r'public\s+(?:sealed\s+)?class\s+(?P<name>\w+Controller)\s*:\s*ControllerBase')
METHOD_RE = re.compile(
    r'public\s+(?:async\s+)?(?:Task(?:<[^>]+>)?|IActionResult|ActionResult(?:<[^>]+>)?)\s+(?P<name>\w+)\s*\('
)
MATRIX_POLICY_RE = re.compile(r'Policy\s*=\s*"(?P<policy>[^"]+)"')
REGISTERED_POLICY_RE = re.compile(r'AddScopedRolePolicy\("(?P<policy>[^"]+)"')


@dataclass(frozen=True)
class RouteEndpoint:
    method: str
    path: str
    controller: str
    action: str
    policies: tuple[str, ...]

    @property
    def operation_id(self) -> str:
        normalized_path = re.sub(
            r"\{(?P<name>[^}:]+)(?::[^}]*)?\}",
            lambda match: f"-by-{match.group('name')}-",
            self.path,
        )
        slug = re.sub(r"[^A-Za-z0-9]+", "-", normalized_path).strip("-").upper()
        return f"OP-REST-{self.method}-{slug}"


def _attributes_before(lines: list[str], index: int) -> str:
    attributes: list[str] = []
    current = index - 1
    while current >= 0:
        line = lines[current].strip()
        if not line:
            current -= 1
            continue
        if line.startswith("["):
            attributes.append(line)
            current -= 1
            continue
        break
    return "\n".join(reversed(attributes))


def _combine_route(base_route: str, action_route: str | None) -> str:
    base = base_route.strip("/")
    action = (action_route or "").strip("/")
    return "/" + "/".join(part for part in (base, action) if part)


def extract_rest_endpoints() -> list[RouteEndpoint]:
    endpoints: list[RouteEndpoint] = []

    for file_path in sorted(CONTROLLERS_ROOT.rglob("*.cs")):
        lines = file_path.read_text(encoding="utf-8-sig").splitlines()
        class_index = next((index for index, line in enumerate(lines) if CLASS_RE.search(line)), None)
        if class_index is None:
            continue

        class_match = CLASS_RE.search(lines[class_index])
        if class_match is None:
            continue

        class_attributes = _attributes_before(lines, class_index)
        route_match = ROUTE_ATTRIBUTE_RE.search(class_attributes)
        if route_match is None:
            continue

        base_route = route_match.group("route")
        class_policies = tuple(match.group("policy") for match in POLICY_RE.finditer(class_attributes))

        for index, line in enumerate(lines[class_index + 1 :], start=class_index + 1):
            method_match = METHOD_RE.search(line)
            if method_match is None:
                continue

            attributes = _attributes_before(lines, index)
            http_match = HTTP_ATTRIBUTE_RE.search(attributes)
            if http_match is None:
                continue

            policies = (*class_policies, *(match.group("policy") for match in POLICY_RE.finditer(attributes)))
            endpoints.append(
                RouteEndpoint(
                    method=http_match.group("method").upper(),
                    path=_combine_route(base_route, http_match.group("route")),
                    controller=class_match.group("name"),
                    action=method_match.group("name"),
                    policies=tuple(dict.fromkeys(policies)),
                )
            )

    return endpoints


def extract_graphql_policies() -> set[str]:
    policies: set[str] = set()
    for file_path in sorted(GRAPHQL_ROOT.rglob("*.cs")):
        policies.update(match.group("policy") for match in POLICY_RE.finditer(file_path.read_text(encoding="utf-8-sig")))
    return policies


def extract_permission_matrix_policies() -> set[str]:
    return {
        match.group("policy")
        for match in MATRIX_POLICY_RE.finditer(PERMISSION_MATRIX.read_text(encoding="utf-8-sig"))
    }


def extract_registered_policies() -> set[str]:
    return {
        match.group("policy")
        for match in REGISTERED_POLICY_RE.finditer(
            AUTHORIZATION_POLICY_EXTENSIONS.read_text(encoding="utf-8-sig")
        )
    }


def render_markdown_inventory(endpoints: list[RouteEndpoint]) -> str:
    lines = [
        "# REST Route Inventory",
        "",
        "Generated from ASP.NET controller attributes. Do not edit manually.",
        "",
        "| Method | Route | Controller action | Policies |",
        "| --- | --- | --- | --- |",
    ]
    for endpoint in endpoints:
        policies = ", ".join(f"`{policy}`" for policy in endpoint.policies) or "Public / endpoint authentication"
        lines.append(
            f"| `{endpoint.method}` | `{endpoint.path}` | `{endpoint.controller}.{endpoint.action}` | {policies} |"
        )
    return "\n".join(lines) + "\n"


def render_operation_catalog(endpoints: list[RouteEndpoint]) -> str:
    """Render stable, generated REST operation evidence for cross-repository contracts."""
    catalog = {
        "catalog_version": 1,
        "generated_from": "IceBot-Backend ASP.NET controller attributes",
        "operations": [
            {
                "id": endpoint.operation_id,
                "transport": "REST",
                "method": endpoint.method,
                "route": endpoint.path,
                "controller": endpoint.controller,
                "action": endpoint.action,
                "authorization_policies": list(endpoint.policies),
            }
            for endpoint in endpoints
        ],
    }
    return json.dumps(catalog, ensure_ascii=True, indent=2) + "\n"


def check_policy_inventory(*, max_failures: int = 30) -> dict:
    endpoints = extract_rest_endpoints()
    used_policies = {policy for endpoint in endpoints for policy in endpoint.policies}
    used_policies.update(extract_graphql_policies())
    matrix_policies = extract_permission_matrix_policies()
    registered_policies = extract_registered_policies()
    unknown_used = sorted(used_policies - registered_policies)
    missing_from_matrix = sorted(registered_policies - matrix_policies)
    stale_matrix_entries = sorted(matrix_policies - registered_policies)
    failures = [
        (
            "IceBot-Backend/src/WebAPI",
            policy,
            "authorization policy is used by REST or GraphQL but absent from AuthorizationPolicyExtensions",
        )
        for policy in unknown_used
    ]
    failures.extend(
        (
            "IceBot-Backend/src/Application/Identity/Roles/Queries/GetPermissionMatrixQueryHandler.cs",
            policy,
            "authorization policy is registered but absent from PermissionMatrixRules",
        )
        for policy in missing_from_matrix
    )
    failures.extend(
        (
            "IceBot-Backend/src/Application/Identity/Roles/Queries/GetPermissionMatrixQueryHandler.cs",
            policy,
            "permission matrix policy is absent from AuthorizationPolicyExtensions",
        )
        for policy in stale_matrix_entries
    )

    return {
        "check": "api_policy_inventory",
        "passed": not failures,
        "rest_endpoint_count": len(endpoints),
        "graphql_policy_count": len(extract_graphql_policies()),
        "registered_policy_count": len(registered_policies),
        "permission_matrix_policy_count": len(matrix_policies),
        "failure_count": len(failures),
        "truncated": len(failures) > max_failures,
        "failures": [
            {
                "file": file_path,
                "line": None,
                "target": policy,
                "reason": reason,
            }
            for file_path, policy, reason in failures[:max_failures]
        ],
    }
