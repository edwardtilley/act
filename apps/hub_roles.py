"""hub_roles service module — store-side client for hub-issued role keys.

The store CONSUMES the hub-issued role keys ``HUB_MARKETING_API_KEY`` and
``HUB_SYSOP_API_KEY`` (pushed into the store's ``.env`` by the hub — CR #13) to
call hub shared services (campaigns, health/backup). These are ONE shared value
across all of the owner's stores, and the store never rotates them.

Transport: the hub's plain-JSON role bridge, ``POST <HUB_URL>/hub/api/role-call``
— it authenticates the same role key against the same registry and dispatches to
the same in-process hub MCP handler under the same (owner, role) identity as the
MCP gateway. Plain JSON keeps this dependency-free (stdlib urllib), matching the
other direct backends in this package.

**Cloud-portable:** this module travels with the store when it is deployed to its
OWN server. The hub is reached over the network via ``HUB_URL`` (e.g.
``https://hub.example.com`` in the cloud; ``http://localhost:5000`` on the dev
box). ``HUB_CALLBACK_URL`` — already set by every store for the Mall-GL mirror —
is used as a fallback, so a deployed store needs no new variable.

Env (store's own ``.env``):
  HUB_URL                 hub base URL (default: ``HUB_CALLBACK_URL``, then
                          ``http://localhost:5000``)
  HUB_MARKETING_API_KEY   marketing role key (hub -> store)
  HUB_SYSOP_API_KEY       sysop role key (hub -> store)

Contract: never raises. Every failure returns ``{'ok': False, 'error': ...}`` so
a store page never 500s on a hub hiccup (the same cache-and-fallback discipline
as ``services/translation.py``).
"""

import json
import os
import urllib.error
import urllib.request

_DEFAULT_URL = "http://localhost:5000"

# Role -> env var name. Add a line here to support a new hub role key.
_ROLE_ENV = {
    "marketing": "HUB_MARKETING_API_KEY",
    "sysop": "HUB_SYSOP_API_KEY",
}


def _base_url() -> str:
    """Hub base URL: HUB_URL wins, then the store's existing HUB_CALLBACK_URL,
    then the dev default. Never hardcode a host — the hub may be local (dev) or
    a public cloud host (https://hub.example.com)."""
    base = (os.environ.get("HUB_URL")
            or os.environ.get("HUB_CALLBACK_URL")
            or _DEFAULT_URL)
    return base.rstrip("/")


def role_key(role: str) -> str:
    """The store's configured key for ``role`` (empty string when unset)."""
    env_name = _ROLE_ENV.get(role, "")
    return (os.environ.get(env_name) or "").strip() if env_name else ""


def call(tool: str, role: str = "marketing", timeout: int = 30, **arguments) -> dict:
    """Call a hub MCP tool over the hub role bridge.

    ``role`` selects which ``HUB_<ROLE>_API_KEY`` to present. ``arguments`` are
    the tool's arguments. Returns the hub's JSON reply
    ``{'ok': True, 'result': ...}`` or ``{'ok': False, 'error': ...}``.
    """
    key = role_key(role)
    if not key:
        return {"ok": False,
                "error": "no %s role key configured (%s)"
                         % (role, _ROLE_ENV.get(role, "?"))}
    payload = json.dumps({"tool": tool, "arguments": arguments}).encode("utf-8")
    req = urllib.request.Request(
        _base_url() + "/hub/api/role-call",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:  # 4xx/5xx carry a JSON body
        try:
            return json.loads(e.read().decode("utf-8", "replace"))
        except (ValueError, OSError):
            return {"ok": False, "error": "hub returned HTTP %s" % e.code}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "error": "hub call failed: %s" % e}


def marketing(tool: str, **arguments) -> dict:
    """Call a hub marketing tool (e.g. ``marketing_campaign_list``)."""
    return call(tool, role="marketing", **arguments)


def sysop(tool: str, **arguments) -> dict:
    """Call a hub sysop tool (e.g. ``health_check``)."""
    return call(tool, role="sysop", **arguments)


def configured_roles() -> list:
    """Roles the store has a key for (for a status/setup page)."""
    return [r for r in _ROLE_ENV if role_key(r)]
