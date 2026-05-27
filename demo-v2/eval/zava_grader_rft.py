"""
Zava RFT Grader - For Reinforcement Fine-Tuning
Fixed based on actual RFT training data format (2026-05-26)

During RFT training, Foundry provides:
- item['messages']: Full conversation array (user + assistant messages)
- item['tools']: Tool calls made during the conversation
- item['expected_resolution']: Expected resolution from dataset
- item[other dataset fields]: All fields from training JSONL

The agent's response is in the last assistant message in item['messages'].
"""

import json
import re


def grade(sample, item):
    """
    Grade agent response for RFT training.
    
    Args:
        sample: Model output metadata (not used in RFT)
        item: Dict with conversation and dataset fields:
              - item['messages']: Conversation array with agent response
              - item['tools']: Tool calls (optional)
              - item['expected_resolution']: Expected resolution from dataset
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    # =========================================================================
    # EXTRACT AGENT RESPONSE from conversation messages
    # =========================================================================
    messages = item.get("messages", [])
    if not messages:
        return 0.0
    
    # Find the last assistant message (agent's response)
    output_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            output_text = msg.get("content", "")
            break
    
    if not output_text:
        return 0.0
    
    # =========================================================================
    # EXTRACT TOOL CALLS (if available)
    # =========================================================================
    output_tools = item.get("tools", []) or []
    
    # =========================================================================
    # EXTRACT EXPECTED RESOLUTION
    # =========================================================================
    expected = item.get("expected_resolution", "")
    if not expected:
        return 0.0
    
    out_lower = output_text.lower()
    exp_lower = expected.lower()
    score = 0.0
    
    # =========================================================================
    # 1. CLARIFICATION SCENARIOS (Policy: clarification)
    # =========================================================================
    if exp_lower.startswith("policy: clarification"):
        # Check if agent asked for clarification and mentioned order ID
        has_clarification = "policy: clarification" in out_lower
        has_order_id = "order id" in out_lower or "order_id" in out_lower
        
        if has_clarification and has_order_id:
            return 1.0  # Perfect clarification response
        elif has_clarification or has_order_id:
            return 0.7  # Partial clarification
        else:
            return 0.3  # Attempted response but wrong
    
    # =========================================================================
    # 2. ACTION SCENARIOS (Specific resolutions)
    # =========================================================================
    
    # Action keywords mapping for different resolution types
    action_keywords = {
        "deny": ["denied", "deny", "not eligible", "cannot", "expired", "unable", "not returnable"],
        "cancel": ["cancel", "cancellation"],
        "store credit": ["store credit", "store_credit"],
        "exchange": ["exchange", "swap"],
        "replacement": ["replacement", "replace"],
        "refund": ["refund"],
    }
    
    # -------------------------------------------------------------------------
    # Component 1: Action/Decision Match (45% weight)
    # -------------------------------------------------------------------------
    # Parse expected actions from expected_resolution (format: "action: refund")
    action_matches = re.findall(r'action:\s*(\w+(?:\s+\w+)?)', exp_lower)
    
    if action_matches:
        hits = 0
        for act in action_matches:
            # Get keywords for this action type
            keywords = action_keywords.get(act.strip(), [act.strip()])
            # Check if any keyword appears in output
            if any(k in out_lower for k in keywords):
                hits += 1
        
        action_score = 0.45 * (hits / len(action_matches))
        score += action_score
    
    # -------------------------------------------------------------------------
    # Component 2: Financial Amount Match (35% weight)
    # -------------------------------------------------------------------------
    # Extract dollar amounts from expected resolution
    exp_amounts = re.findall(r'\$(\d+\.?\d{0,2})', expected)
    non_zero = [a for a in exp_amounts if float(a) > 0.0]
    
    if non_zero:
        # Extract dollar amounts from output (with optional space after $)
        out_amounts = re.findall(r'\$\s*(\d+(?:\.\d{1,2})?)', output_text)
        out_floats = {round(float(a), 2) for a in out_amounts}
        
        # Check each expected amount is present (with 2 cent tolerance)
        hits = sum(1 for a in non_zero if any(abs(float(a) - o) < 0.02 for o in out_floats))
        amount_score = 0.35 * (hits / len(non_zero))
        score += amount_score
    else:
        # No amounts expected, give partial credit
        score += 0.15
    
    # -------------------------------------------------------------------------
    # Component 3: Tool Usage (20% weight)
    # -------------------------------------------------------------------------
    # Check that agent used key tools appropriately
    if output_tools:
        # Handle different tool call formats
        tool_names = []
        for t in output_tools:
            if isinstance(t, dict):
                # Try different possible structures
                name = (
                    t.get("name") or 
                    t.get("function", {}).get("name") or
                    t.get("tool_name") or
                    ""
                )
                if name:
                    tool_names.append(name)
        
        # Key tools expected for most scenarios
        key_tools = [
            "get_order_details",        # Always needed to understand the order
            "check_resolution_policy",  # Needed to know what's allowed
            "calculate_resolution"      # Needed to compute amounts
        ]
        
        # Count how many key tools were used
        hits = sum(1 for t in key_tools if t in tool_names)
        tool_score = 0.20 * (hits / len(key_tools))
        score += tool_score
    
    # =========================================================================
    # FINAL SCORE
    # =========================================================================
    # Cap at 1.0 and round to 3 decimals
    final_score = round(min(score, 1.0), 3)
    
    return final_score


# =============================================================================
# GRADER METADATA (for reference)
# =============================================================================
# Pass Threshold: 0.80 (scenarios scoring ≥0.80 count as "success")
# Scoring Breakdown:
#   - Action/Decision Match: 45% (correct refund/exchange/deny/etc.)
#   - Financial Amounts: 35% (correct dollar amounts within 2¢)
#   - Tool Usage: 20% (used get_order_details, check_policy, calculate)
#
# Special Cases:
#   - Clarification scenarios: Full score if asks for order ID
#   - Zero-amount scenarios: 15% amount credit (since no amounts to verify)
#
# Data Format (RFT Training):
#   - item['messages']: Array of conversation messages
#   - item['tools']: Array of tool calls
#   - item['expected_resolution']: Ground truth from dataset
# =============================================================================
