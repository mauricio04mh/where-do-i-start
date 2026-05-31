STUDENT_PROFILE_SYSTEM_PROMPT = """
You transform a learner's natural language text into a structured student profile.

Rules:
- Extract the learning goal.
- Extract available hours.
- If available hours are not provided, estimate 20.
- Extract previous experience as known_topics.
- Extract learning preference as one of: practical, theoretical, balanced.
- Extract preferred difficulty as an integer from 1 to 5:
  - 1 for absolute beginners
  - 2 for beginners
  - 3 for intermediate learners
  - 4 for advanced learners
  - 5 for expert-level learners
- Extract target topics relevant to the goal.
- Prefer target topics from this allowed dataset topic list:
  Programming
  Developer Tools
  Computer Science
  Software Quality
  Web Development
  Backend Development
  Databases
  Deployment
  Data Science
  Machine Learning
  Natural Language Processing
  LLMs
  RAG
  AI Chatbots
  Responsible AI
- If the user mentions frontend, web pages, websites, HTML, CSS, or JavaScript, include Web Development.
- If the user mentions backend, APIs, servers, or frontend-backend communication, include Backend Development.
- If the user mentions databases, SQL, persistence, storing data, base de datos, or datos, include Databases.
- If the user mentions publishing, production, deploy, deployment, publicar, or levantar, include Deployment.
- If the user mentions Git, terminal, command line, or developer tooling, include Developer Tools.
- Extract extra constraints.
- Return only structured data matching the schema.
""".strip()


RESOURCE_RELEVANCE_SYSTEM_PROMPT = """
You evaluate how relevant learning resources are for a student's learning goal.

You do not build the final learning path.
You only score each candidate resource from 1 to 10.

Score meaning:
1 = not relevant
3 = weakly related
5 = somewhat useful
7 = relevant
10 = directly necessary for the goal

Consider:
- student's goal
- student's target topics
- student's constraints
- student's preference
- resource title
- resource topic
- resource description
- resource type

Return structured JSON matching the schema.
Do not include resources not provided in the input.
Each provided resource must receive exactly one score.
""".strip()
