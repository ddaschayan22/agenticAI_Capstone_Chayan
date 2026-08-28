Problem 18 : 

Ticket Intelligence System - Multi-Hop Reasoning, Jira via MCP, Multi-Model Agents and Memory.



You already built a multi-hop agent with a Planner and an Executor that can answer compound questions like "which customers had the same login issue as ticket 4021, and did any of them churn afterward" by breaking the question into steps and executing them one at a time. Support leads now want that system to do more than answer questions, they want it to act on what it finds, remember what it's already told them, and stop treating every question as if it's the first one anyone ever asked.



Right now, when your agent identifies that three customers had ticket 4021's login issue and one of them churned, that finding just gets printed back to the user and forgotten. The support team wants a Jira ticket automatically created for that churned customer's issue category, tagged for follow-up, and they want it done through a proper MCP connection to Jira, not a one-off API call bolted onto the Executor. Add an MCP server that exposes Jira as a tool, create ticket, update ticket, search existing tickets by category, and give the Executor Agent access to that MCP client so that once a step in the plan surfaces something actionable, it can create or update the corresponding Jira issue as part of executing that step, not as a separate manual process afterward.



Right now your Planner and Executor are two roles, but nothing stops them both from being the same underlying model doing two jobs. Split this into a proper multi-agent system where each agent uses the model actually suited to its job: the Planner needs strong structured reasoning to decompose a compound question correctly, so give it your strongest available model, the Executor's per-step relevance grading and retry logic is a simpler, high-volume job that runs many times per query, so route it to a smaller, cheaper model, and the new Jira Agent handling ticket creation and updates is mostly structured field-filling, which a lightweight model handles fine too. The point isn't just adding a third agent, it's proving your architecture doesn't assume one model for everything, each agent should be swappable independently based on what its job actually requires.



Finally, this system needs to stop being amnesiac between runs. Add three distinct layers of memory, not one generic memory blob. Short-term memory holds the current question's plan and the results gathered so far in this one run, exactly what the Executor already needs step to step. Working memory holds the intermediate state of whichever step is currently in progress, the partial retrievals and retries for that one step specifically, and gets cleared once that step completes, it should never leak into the next step's context. Long-term memory persists across sessions entirely, if the system already flagged a customer as a churn risk and created a Jira ticket for them last week, it needs to remember that the next time a related question comes in, so it doesn't create a duplicate ticket or re-report the same finding as if it were new.



Test the full system against three cases. First, a compound question that resolves across multiple plan steps and results in a genuinely new finding, confirm a Jira ticket gets created through MCP with the correct fields. Second, ask a related question about the same customer a second time in a later session, confirm long-term memory stops the system from duplicating the Jira ticket or re-announcing the same finding as new. Third, ask a compound question where a required piece of information doesn't exist in your data, confirm the agent says plainly what it couldn't find rather than fabricating it or creating a Jira ticket on incomplete information. If all three behave correctly, and you can show the Planner's plan, the Executor's step-by-step execution with its Jira actions, and the difference between what long-term memory recalled versus what was found fresh, you're done.





jira token: 



how many agents are required. Plan for the execution . Please give realistic agent names easily understandable by humans.  Please give execution plan for below requirement:



