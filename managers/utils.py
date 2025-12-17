
from difflib import SequenceMatcher

def similar(a, b):
    """Returns a similarity score between 0 and 1."""
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(target, candidates, threshold=0.6):
    """
    Finds the best match for 'target' string in a list of 'candidates'.
    Candidates can be a list of strings or a list of dicts (if key provided, but let's keep it simple).
    Returns (best_match_item, score) or (None, 0).
    """
    best_score = 0
    best_match = None
    
    target = target.lower()
    
    for cand in candidates:
        # Assuming cand is a dict with a 'title' or 'question' field, or just a string
        # Let's assume cand is a dict and we check 'title'
        c_text = cand.get("title", "").lower()
        if not c_text:
             continue
             
        score = similar(target, c_text)
        
        if score > best_score:
            best_score = score
            best_match = cand
            
    if best_score >= threshold:
        return best_match, best_score
    
    return None, best_score
