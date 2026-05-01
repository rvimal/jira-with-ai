@startuml
!theme cerulean-outline

title Automated Jira Priority Scorer - Architecture

' Global Formatting
skinparam componentStyle uml2
skinparam DatabaseBackgroundColor #f9f9f9
skinparam NoteBackgroundColor #fff5ad
skinparam actor {
    BackgroundColor #e0f7fa
    BorderColor #006064
}

' Components
package "Automation Layer" {
    [OS Scheduler / Cron] as Scheduler #lightgreen
    [CLI Orchestrator] as LogicEngine #strategy
}

package "Logic & Context" {
    artifact "Prioritization_Prompts.md" as Prompts
    artifact "Scoring_rule_Prompts.md & sample_example.csv" as Criteria
}

node "Model Context Protocol (MCP)" {
    [Jira MCP Server] as JiraMCP
}

cloud "AI Engine" {
    [GPT OSS Model] as LLM
}

database "Atlassian" {
    [Jira Backlog] as JiraDB
}

' Workflow Interactions
Scheduler --> LogicEngine : 1. Triggers Periodic Job (e.g., Hourly)

LogicEngine ..> Prompts : 2. Loads System Instructions
LogicEngine ..> Criteria : 3. Loads Scoring Logic

' Data Fetching
LogicEngine <--> JiraMCP : 4. Requests Backlog Items
JiraMCP <--> JiraDB : 5. Fetch Tickets (JQL)

' Reasoning
LogicEngine <--> LLM : 6. Analyze Tickets vs. Criteria\n(Calculate Priority Score)

' Writing back to Jira
LogicEngine --> JiraMCP : 7. Update 'Score' Field
JiraMCP --> JiraDB : 8. POST /issue/{id} (Update)



@enduml