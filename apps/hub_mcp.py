"""Hub MCP client — consume hub shared services from the store.

Presents this store's role keys to the hub's MCP streamable-HTTP gateway
(``HUB_MCP_URL``, default ``http://ubuntu:5001/mcp``) per call. No login or
persistent session is kept.

Key model (see AGENTS.md §11):

* ``STORE_AI_DEVELOPER_API_KEY`` — this store's OWN identity (store -> hub),
  unique per store; used by the store's IDE agent (change requests, health).
* ``HUB_MARKETING_API_KEY`` / ``HUB_SYSOP_API_KEY`` — hub-issued role keys
  injected INTO this store by the hub (hub -> store); the same value across
  all the owner's stores. The store consumes them and never rotates them.

The marketing helpers are gated: when ``HUB_MARKETING_API_KEY`` is unset the
store is not opted in and calls raise :class:`HubMCPError`.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from django.conf import settings

# env var name per hub role
ROLE_KEYS = {
    'ai_developer': 'STORE_AI_DEVELOPER_API_KEY',
    'marketing': 'HUB_MARKETING_API_KEY',
    'sysop': 'HUB_SYSOP_API_KEY',
}


class HubMCPError(Exception):
    """Raised when the hub gateway is unreachable or the tool call fails."""


def _gateway_url():
    return (getattr(settings, 'HUB_MCP_URL', '') or 'http://ubuntu:5001/mcp').strip()


def _key_for(role):
    var = ROLE_KEYS.get(role)
    if not var:
        raise HubMCPError('unknown hub role %r' % role)
    key = (getattr(settings, var, '') or '').strip()
    if not key:
        raise HubMCPError(
            '%s is not set — this store is not opted in to the hub %r '
            'shared service.' % (var, role)
        )
    return key


def _post(payload, session_id=None, timeout=30):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    }
    if session_id:
        headers['mcp-session-id'] = session_id
    req = urllib.request.Request(
        _gateway_url(), data=json.dumps(payload).encode('utf-8'),
        headers=headers, method='POST',
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise HubMCPError('hub MCP HTTP %s: %s' % (e.code, e.reason)) from e
    except urllib.error.URLError as e:
        raise HubMCPError('hub MCP gateway unreachable: %s' % e) from e
    return resp.read().decode('utf-8'), resp.headers.get('mcp-session-id')


def _extract_json(body):
    """Streamable-HTTP responses are SSE (``data: {...}``) or raw JSON."""
    text = body or ''
    m = re.search(r'data:\s*(\{.*\})', text, re.S)
    if m:
        text = m.group(1)
    return json.loads(text)


def call_tool(name, arguments=None, role='ai_developer', timeout=30):
    """Call a hub MCP tool under ``role``'s key. Returns the tool's data.

    Raises :class:`HubMCPError` on a missing key, transport failure, or a
    tool-level error response.
    """
    key = _key_for(role)
    args = dict(arguments or {})
    args['api_key'] = key

    # Initialize the session (the gateway requires an initialized session).
    _, session_id = _post({
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05', 'capabilities': {},
            'clientInfo': {'name': 'advance-store', 'version': '1.0'},
        },
    }, timeout=timeout)
    _post(
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        session_id=session_id, timeout=timeout,
    )

    body, _ = _post({
        'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
        'params': {'name': name, 'arguments': args},
    }, session_id=session_id, timeout=timeout)

    try:
        payload = _extract_json(body)
    except (ValueError, TypeError) as e:
        raise HubMCPError('bad hub MCP response: %s' % (body or '')[:200]) from e

    result = payload.get('result') or {}
    content = result.get('content') or []
    if result.get('isError'):
        msg = content[0].get('text') if content else 'hub tool error'
        raise HubMCPError(msg)
    if content:
        raw = content[0].get('text', '')
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return raw
    return result


def marketing_enabled():
    """True when the store is opted in to the hub marketing shared service."""
    return bool((getattr(settings, 'HUB_MARKETING_API_KEY', '') or '').strip())


# ── Marketing tools (hub 'marketing' role) ────────────────────────────────
# Thin pass-through wrappers; callers pass the tool's own params as kwargs.

def marketing_campaign_list(**kwargs):
    return call_tool('marketing_campaign_list', kwargs, role='marketing')


def marketing_campaign_get(campaign_id, **kwargs):
    kwargs['campaign_id'] = campaign_id
    return call_tool('marketing_campaign_get', kwargs, role='marketing')


def marketing_campaign_create(**kwargs):
    return call_tool('marketing_campaign_create', kwargs, role='marketing')


def marketing_campaign_update(**kwargs):
    return call_tool('marketing_campaign_update', kwargs, role='marketing')


def marketing_entry_list(**kwargs):
    return call_tool('marketing_entry_list', kwargs, role='marketing')


def marketing_entry_add(**kwargs):
    return call_tool('marketing_entry_add', kwargs, role='marketing')


def marketing_entry_update(**kwargs):
    return call_tool('marketing_entry_update', kwargs, role='marketing')


def marketing_entry_approve(entry_id, **kwargs):
    kwargs['entry_id'] = entry_id
    return call_tool('marketing_entry_approve', kwargs, role='marketing')


def marketing_entry_send(entry_id, **kwargs):
    kwargs['entry_id'] = entry_id
    return call_tool('marketing_entry_send', kwargs, role='marketing')


def marketing_contacts_list(**kwargs):
    return call_tool('marketing_contacts_list', kwargs, role='marketing')


def marketing_contact_upsert(**kwargs):
    return call_tool('marketing_contact_upsert', kwargs, role='marketing')


def marketing_sweep_sheets(**kwargs):
    return call_tool('marketing_sweep_sheets', kwargs, role='marketing')


def marketing_unsent_list(**kwargs):
    return call_tool('marketing_unsent_list', kwargs, role='marketing')
