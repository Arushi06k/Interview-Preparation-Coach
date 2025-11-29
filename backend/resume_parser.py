from config import DOMAIN_SKILL_MAP
from collections import defaultdict

# Renamed function for clarity
def get_ranked_domains(text: str) -> list:
    """
    Analyzes resume text and returns a list of ALL identified domains,
    ranked by the number of skills found.
    """
    domain_scores = defaultdict(lambda: {"score": 0, "skills_found": set()})
    text_lower = text.lower()
    
    # 1. Score all domains based on skill matches
    for domain, skills in DOMAIN_SKILL_MAP.items():
        for skill in skills:
            # Check if the skill keyword exists in the resume text
            if skill in text_lower:
                domain_scores[domain]["score"] += 1
                domain_scores[domain]["skills_found"].add(skill.capitalize())
                
    if not domain_scores:
        return []

    # 2. Sort ALL domains by score, descending (highest score first)
    sorted_domains = sorted(
        domain_scores.items(), 
        key=lambda item: item[1]['score'], 
        reverse=True
    )
    
    ranked_domains = []
    
    # 3. Compile the final list, including ALL domains with a score > 0
    for domain_name, data in sorted_domains:
        if data['score'] > 0: # Only include domains where skills were actually found
            ranked_domains.append({
                "domain_name": domain_name,
                "skills_found": list(data["skills_found"])
            })
        
    # *** CRITICAL: The list is NOT sliced here, ensuring ALL are returned. ***
    return ranked_domains