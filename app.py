def seniority_confidence(skills, level):
    score = len(skills) * 8
    base = {"Junior": 40, "Mid": 60, "Senior": 80}[level]
    return min(95, base + score)

def skill_gap_analysis(found, jd_text):
    jd_text = jd_text.lower()
    must_have = ["python", "sql", "cloud", "docker", "kubernetes"]
    missing = [s for s in must_have if s not in jd_text]
    return missing

def interview_focus(skills):
    focus = []
    for s in skills:
        if s in ["AWS", "Azure", "Docker", "Kubernetes"]:
            focus.append("Production deployment & scalability")
        elif s in ["React"]:
            focus.append("Frontend system design")
        elif s in ["Machine Learning"]:
            focus.append("Model evaluation & data pipelines")
        else:
            focus.append("Problem solving depth")
    return list(set(focus))

def culture_hint(jd):
    jd = jd.lower()
    if "startup" in jd or "fast-paced" in jd:
        return "Startup-style environment. Look for adaptability & ownership."
    if "enterprise" in jd or "process" in jd:
        return "Enterprise environment. Look for documentation & collaboration."
    return "Balanced team culture. Probe communication & initiative."

def risk_flags(jd, skills):
    flags = []
    if len(skills) < 3:
        flags.append("JD too vague on technical stack.")
    if "everything" in jd or "all" in jd:
        flags.append("Overloaded role expectations.")
    if "immediate joiner" in jd:
        flags.append("Urgent hiring — may compromise screening.")
    return flags if flags else ["No major red flags detected."]

def hiring_signal(confidence, missing):
    if confidence > 80 and not missing:
        return "🟢 Strong hire potential."
    if confidence > 60:
        return "🟡 Moderate fit — probe gaps."
    return "🔴 High risk — evaluate carefully."

def hiring_recommendation(confidence, missing):
    if confidence > 80 and not missing:
        return "Proceed directly to deep technical rounds."
    if confidence > 60:
        return "Proceed with caution. Validate missing skills."
    return "Screen thoroughly before advancing."
