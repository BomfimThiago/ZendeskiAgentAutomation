I'm going to put here a little bit of my strategy and decisions for this homework.

1 - First, I decided to implement an integration with Zendesk. For that, I had to create a company, TeleCorp, that specializes in services for Internet and Mobile. It offers some plans. I created a knowledge base so the company had a background. Also, I decided to build a FastAPI because it's already async, making it easier to handle a lot of async processes we need to work with agents and tools.

2 - Then I decided to use multi-agents with LangGraph. Multi-agents because it made sense to have specialized agents for different user needs. LangGraph because it's one of the best frameworks to build agents.

3 - I built agents for Billing, Support, and Sales, using a Supervisor strategy. First, I tried to have a general supervisor that classifies the user intent and routes them to one of the agents. Then I changed to make the Supervisor already the Sales Agent. It made more sense thinking that if a customer got in contact, we already had to treat them as a potential LEAD and get information to contact them in the future.

4 - The agents should recognize if the user is new or already existing and then create or get information in Zendesk.

5 - Zendesk is a beast with so many functionalities. I decided to focus only on getting tickets and creating tickets for this homework, knowing perfectly well that there are so many functionalities that I could have explored, like personalization of tickets, integrations with emails, Slack, webhooks that I could have implemented, and putting an agent to resolve a ticket. However, I wanted to keep the scenarios controllable.

6 - I could also have built a knowledge base inside Zendesk and built agent tools to access this knowledge base, using RAG or Agentic-RAG. What I did was a mini version of Agentic-RAG in a controlled version. So I put the documents locally, got information from the files, and passed it to the context of the model, controlling the context length with chunks and summarization. I just wanted to give an idea. Probably in production I would have to design a complete RAG, Agentic-RAG, or GRAPH-RAG approach since this will be the core of a good answer from the model to the user.

7 - I also wanted to give an idea of the security against prompt injection and out-of-scope intents. There is probably so much room to improve, but the idea is there. Knowing that we cannot resolve AI security problems with more AI, one reference that I like is here: https://simonwillison.net/2022/Sep/17/prompt-injection-more-ai/. In production, we would have to build a whole security strategy.

8 - LangGraph has complex state management and checkpoints. I implemented a small version that can be improved. Also, the multi-agent architecture can be improved with reasoning strategies like ReAct, Plan-and-Execute, or others. Also, memory and context should be more controlled. I didn't use caching, and my sessions were controlled to one user. For several users, we would need memory and context control for different users as well as caching for performance.

9 - I used a lot of LangSmith to understand how the agents were working. For my development case, it replaced the unit tests. However, for production, unit testing the agents is necessary.

10 - I didn't use any database because Zendesk is the center of the tickets. For more functionality, a database would be necessary, or even a vector or graph database for a RAG system.

11 - I did build some API endpoints just to test if the connection with Zendesk was working before doing an agent tool.

12 - I could also have explored MCP servers for this. In production, maybe we would build an MCP server with Zendesk tools.


There's a lot I could do, but it made sense to keep it simple for me. Hopefully, this is everything I need for this homework and gives an idea of how powerful a multi-agent system with tools and integration with Zendesk can be.