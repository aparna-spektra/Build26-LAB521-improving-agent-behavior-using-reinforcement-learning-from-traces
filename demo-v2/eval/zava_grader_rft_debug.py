"""
Zava RFT Grader - Debug Version with Logging
Adding comprehensive error handling and logging to diagnose zero scores
"""

import json
import re


def grade(sample, item):
    """
    Grade agent response for RFT training with debug logging.
    """
    # Debug: Log what we receive
    debug_info = {
        "sample_keys": list(sample.keys()) if isinstance(sample, dict) else "not_dict",
        "item_keys": list(item.keys()) if isinstance(item, dict) else "not_dict",
    }
    
    # Try to extract messages from different possible locations
    messages = None
    output_text = ""
    
    # Option 1: item['messages']
    if 'messages' in item:
        messages = item.get('messages', [])
        debug_info['messages_found'] = 'item'
        debug_info['messages_count'] = len(messages) if isinstance(messages, list) else 0
    
    # Option 2: sample['messages']
    elif 'messages' in sample:
        messages = sample.get('messages', [])
        debug_info['messages_found'] = 'sample'
        debug_info['messages_count'] = len(messages) if isinstance(messages, list) else 0
    
    # Option 3: Check if there's output_text directly
    if 'output_text' in item:
        output_text = item.get('output_text', '')
        debug_info['output_text_found'] = 'item.output_text'
    elif 'sample.output_text' in item:
        output_text = item.get('sample.output_text', '')
        debug_info['output_text_found'] = 'item.sample.output_text'
    elif 'output_text' in sample:
        output_text = sample.get('output_text', '')
        debug_info['output_text_found'] = 'sample.output_text'
    
    # Extract from messages if we have them and no direct output_text
    if not output_text and messages:
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                output_text = msg.get("content", "")
                debug_info['output_extracted_from'] = 'messages'
                break
    
    # Check if we have output text
    if not output_text:
        # Return small non-zero score with debug info in case of no output
        debug_info['error'] = 'no_output_text_found'
        # In production, we'd log this. For now, return 0.0
        return 0.0
    
    debug_info['output_text_length'] = len(output_text)
    
    # Extract expected resolution
    expected = item.get("expected_resolution", "")
    if not expected:
        debug_info['error'] = 'no_expected_resolution'
        return 0.0
    
    debug_info['expected_resolution_length'] = len(expected)
    
    # =========================================================================
    # SCORING LOGIC
    # =========================================================================
    out_lower = output_text.lower()
    exp_lower = expected.lower()
    score = 0.0
    
    # 1. CLARIFICATION SCENARIOS
    if exp_lower.startswith("policy: clarification"):
        has_clarification = "policy: clarification" in out_lower
        has_order_id = "order id" in out_lower or "order_id" in out_lower
        
        if has_clarification and has_order_id:
            return 1.0
        elif has_clarification or has_order_id:
            return 0.7
        else:
            return 0.3
    
    # 2. ACTION SCENARIOS
    action_keywords = {
        "deny": ["denied", "deny", "not eligible", "cannot", "expired", "unable", "not returnable"],
        "cancel": ["cancel", "cancellation"],
        "store credit": ["store credit", "store_credit"],
        "exchange": ["exchange", "swap"],
        "replacement": ["replacement", "replace"],
        "refund": ["refund"],
    }
    
    # Action matching
    action_matches = re.findall(r'action:\s*(\w+(?:\s+\w+)?)', exp_lower)
    if action_matches:
        hits = 0
        for act in action_matches:
            keywords = action_keywords.get(act.strip(), [act.strip()])
            if any(k in out_lower for k in keywords):
                hits += 1
        score += 0.45 * (hits / len(action_matches))
    
    # Amount matching
    exp_amounts = re.findall(r'\$(\d+\.?\d{0,2})', expected)
    non_zero = [a for a in exp_amounts if float(a) > 0.0]
    
    if non_zero:
        out_amounts = re.findall(r'\$\s*(\d+(?:\.\d{1,2})?)', output_text)
        out_floats = {round(float(a), 2) for a in out_amounts}
        hits = sum(1 for a in non_zero if any(abs(float(a) - o) < 0.02 for o in out_floats))
        score += 0.35 * (hits / len(non_zero))
    else:
        score += 0.15
    
    # Tool usage
    output_tools = item.get("tools", []) or []
    if output_tools:
        tool_names = []
        for t in output_tools:
            if isinstance(t, dict):
                name = (
                    t.get("name") or 
                    t.get("function", {}).get("name") or
                    t.get("tool_name") or
                    ""
                )
                if name:
                    tool_names.append(name)
        
        key_tools = ["get_order_details", "check_resolution_policy", "calculate_resolution"]
        hits = sum(1 for t in key_tools if t in tool_names)
        score += 0.20 * (hits / len(key_tools))
    
    final_score = round(min(score, 1.0), 3)
    return final_score
