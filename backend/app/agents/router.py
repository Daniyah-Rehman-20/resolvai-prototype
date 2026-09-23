def needs_policy_evidence(issue_type: str) -> bool:
    return issue_type not in {"SUCCESS", "REFUNDED"}
