print("=== HR Prompt Engineering Tool v1 ===\n")
print("Paste Job Description below.")
print("Type END and press Enter when finished:\n")

# ---------- INPUT JD ----------
lines = []
while True:
    line = input()
    if line.strip().upper() == "END":
        break
    lines.append(line)

jd = "\n".join(lines)

# ---------- PROCESSING ----------
tech_qs = [
    "Explain CI/CD pipelines and their importance.",
    "How would you deploy a Python app using Docker?",
    "What is Kubernetes and where have you used it?",
    "Explain rollback strategies in deployments.",
    "How do you monitor production systems?"
]

behav_qs = [
    "Describe a time you solved a hard technical problem.",
    "How do you handle tight deadlines?",
    "Tell about a conflict in your team.",
    "How do you learn new technologies?",
    "Explain a failure and what you learned."
]

tasks = [
    "Build a simple CI/CD pipeline for a Python application.",
    "Deploy an application using Docker + Kubernetes.",
    "Write a system design document for scalable deployment."
]

rubric = {
    "Technical Skill": "40%",
    "Problem Solving": "25%",
    "System Design": "20%",
    "Communication": "15%"
}

# ---------- DISPLAY ----------
print("\n=========== OUTPUT ===========\n")

print(" TECHNICAL QUESTIONS")
for q in tech_qs:
    print("-", q)

print("\n BEHAVIORAL QUESTIONS")
for q in behav_qs:
    print("-", q)

print("\n ASSESSMENT TASKS")
for t in tasks:
    print("-", t)

print("\n SCORING RUBRIC")
for k, v in rubric.items():
    print(f"{k}: {v}")

# ---------- SAVE TO FILE ----------
output = []

output.append("HR PROMPT ENGINEERING TOOL REPORT\n")
output.append("\nJOB DESCRIPTION:\n" + jd)

output.append("\nTECHNICAL QUESTIONS:\n")
for q in tech_qs:
    output.append(q)

output.append("\nBEHAVIORAL QUESTIONS:\n")
for q in behav_qs:
    output.append(q)

output.append("\nASSESSMENT TASKS:\n")
for t in tasks:
    output.append(t)

output.append("\nSCORING RUBRIC:\n")
for k, v in rubric.items():
    output.append(f"{k}: {v}")

with open("report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("\n Report saved as report.txt in project folder.\n")
