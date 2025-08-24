#!/usr/bin/env python3
"""
Feature Research and PRD Generation Agent - FastAPI Server

This server provides a REST API for:
1. Researching features by searching the web
2. Creating detailed PRDs in Notion
3. Creating issues and tasks in Linear
4. Monitoring and managing Linear comments
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, SecretStr
from dotenv import load_dotenv
from portia import (
    Portia, 
    Config, 
    PlanBuilder, 
    PlanRunState, 
    Clarification,
    ClarificationHandler,
    ActionClarification,
    InputClarification,
    MultipleChoiceClarification,
    ValueConfirmationClarification,
    CustomClarification,
    ExecutionHooks,
    PortiaToolRegistry
)

# Load environment variables
load_dotenv()

# Check for required environment variables
portia_api_key = os.getenv('PORTIA_API_KEY')
if not portia_api_key:
    print("❌ Error: PORTIA_API_KEY environment variable is required")
    print("Please set PORTIA_API_KEY in your .env file")
    print("You can get your API key from: https://app.portialabs.ai > API Keys")
    exit(1)

# Set the environment variable explicitly to ensure it's available
os.environ['PORTIA_API_KEY'] = portia_api_key

# Initialize FastAPI app
app = FastAPI(
    title="Feature Research Agent API",
    description="API for researching features, creating PRDs, and managing Linear issues",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for tracking research sessions
research_sessions = {}

# Pydantic models for API requests/responses
class FeatureRequest(BaseModel):
    """A feature request with name and description."""
    name: str = Field(..., description="The name of the feature")
    description: str = Field(..., description="Detailed description of the feature")

class ResearchResult(BaseModel):
    """A research result from web search."""
    title: str = Field(..., description="Title of the article/blog/news")
    url: str = Field(..., description="URL of the source")
    summary: str = Field(..., description="Summary of the content")
    relevance_score: int = Field(..., description="Relevance score from 1-10")
    key_insights: List[str] = Field(..., description="Key insights from this source")

class FeatureAnalysis(BaseModel):
    """Comprehensive analysis of a feature."""
    feature_name: str = Field(..., description="Name of the feature")
    description: str = Field(..., description="Description of the feature")
    research_sources: List[ResearchResult] = Field(..., description="Research sources found")
    market_analysis: str = Field(..., description="Market analysis and trends")
    technical_considerations: List[str] = Field(..., description="Technical considerations")
    implementation_approaches: List[str] = Field(..., description="Possible implementation approaches")
    risks_and_challenges: List[str] = Field(..., description="Risks and challenges")
    success_metrics: List[str] = Field(..., description="Success metrics to track")
    recommendations: str = Field(..., description="Overall recommendations")

class PRDContent(BaseModel):
    """Content for the Product Requirements Document."""
    title: str = Field(..., description="PRD title")
    executive_summary: str = Field(..., description="Executive summary")
    problem_statement: str = Field(..., description="Problem being solved")
    solution_overview: str = Field(..., description="Solution overview")
    user_stories: List[str] = Field(..., description="User stories")
    acceptance_criteria: List[str] = Field(..., description="Acceptance criteria")
    technical_requirements: List[str] = Field(..., description="Technical requirements")
    design_considerations: List[str] = Field(..., description="Design considerations")
    timeline: str = Field(..., description="Estimated timeline")
    dependencies: List[str] = Field(..., description="Dependencies")

class NotionPageOutput(BaseModel):
    """Output schema for Notion page creation."""
    page_id: str = Field(..., description="The ID of the created Notion page")

class LinearTaskOutput(BaseModel):
    """Output schema for individual Linear task creation."""
    task_id: str = Field(..., description="The ID of the created Linear task")
    title: str = Field(..., description="The title of the task")
    description: str = Field(..., description="The description of the task")

class LinearCommentOutput(BaseModel):
    """Output schema for Linear comment operations (create/update)."""
    comment_id: str = Field(..., description="The ID of the comment")
    content: str = Field(..., description="The content of the comment")

class LinearCommentsListOutput(BaseModel):
    """Output schema for listing Linear comments."""
    content: List[dict] = Field(..., description="List of comment objects")
    meta: dict = Field(..., description="Metadata about the response")
    isError: bool = Field(..., description="Whether the response is an error")

class LinearIssueOutput(BaseModel):
    """Output schema for Linear issue creation."""
    issue_id: str = Field(..., description="The ID of the created Linear issue")
    title: str = Field(..., description="The title of the issue")
    description: str = Field(..., description="The description of the issue")
    tasks: List[LinearTaskOutput] = Field(default_factory=list, description="List of created tasks")

class CommentRequest(BaseModel):
    """Request to create a new comment."""
    issue_id: str = Field(..., description="Linear issue ID")
    title: str = Field(..., description="Comment title")
    content: str = Field(..., description="Comment content")

class CommentResponse(BaseModel):
    """Response for comment operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ResearchSessionResponse(BaseModel):
    """Response for research session status."""
    session_id: str = Field(..., description="Unique session ID")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Research results")
    error: Optional[str] = Field(None, description="Error message if any")

# Clarification handler for the feature research agent
class FeatureResearchClarificationHandler(ClarificationHandler):
    """Handles clarifications for the feature research agent."""
    
    def handle_action_clarification(
        self,
        clarification: ActionClarification,
        on_resolution: Callable[[Clarification, object], None],
        on_error: Callable[[Clarification, object], None],
    ) -> None:
        """Handle action clarifications (e.g., OAuth flows)."""
        print(f"\n🔐 ACTION REQUIRED: {clarification.user_guidance}")
        if hasattr(clarification, 'action_url'):
            print(f"📎 Action URL: {clarification.action_url}")
        print("Please complete the required action and then press Enter to continue...")
        input("Press Enter when ready...")
        on_resolution(clarification, "completed")

    def handle_input_clarification(
        self,
        clarification: InputClarification,
        on_resolution: Callable[[Clarification, object], None],
        on_error: Callable[[Clarification, object], None],
    ) -> None:
        """Handle input clarifications."""
        print(f"\n❓ INPUT NEEDED: {clarification.user_guidance}")
        if hasattr(clarification, 'argument_name'):
            print(f"Parameter: {clarification.argument_name}")
        user_input = input("Please provide the required input: ")
        on_resolution(clarification, user_input)

    def handle_multiple_choice_clarification(
        self,
        clarification: MultipleChoiceClarification,
        on_resolution: Callable[[Clarification, object], None],
        on_error: Callable[[Clarification, object], None],
    ) -> None:
        """Handle multiple choice clarifications."""
        print(f"\n🤔 CHOOSE AN OPTION: {clarification.user_guidance}")
        if hasattr(clarification, 'options') and clarification.options:
            for i, option in enumerate(clarification.options, 1):
                print(f"{i}. {option}")
            while True:
                try:
                    choice = int(input(f"Please select an option (1-{len(clarification.options)}): "))
                    if 1 <= choice <= len(clarification.options):
                        selected_option = clarification.options[choice - 1]
                        on_resolution(clarification, selected_option)
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(clarification.options)}")
                except ValueError:
                    print("Please enter a valid number")
        else:
            user_input = input("Your choice: ")
            on_resolution(clarification, user_input)

    def handle_value_confirmation_clarification(
        self,
        clarification: ValueConfirmationClarification,
        on_resolution: Callable[[Clarification, object], None],
        on_error: Callable[[Clarification, object], None],
    ) -> None:
        """Handle value confirmation clarifications."""
        print(f"\n✅ CONFIRM VALUE: {clarification.user_guidance}")
        if hasattr(clarification, 'value_to_confirm'):
            print(f"Value to confirm: {clarification.value_to_confirm}")
        response = input("Is this correct? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            on_resolution(clarification, True)
        else:
            on_error(clarification, "User rejected the value")

    def handle_custom_clarification(
        self,
        clarification: CustomClarification,
        on_resolution: Callable[[Clarification, object], None],
        on_error: Callable[[Clarification, object], None],
    ) -> None:
        """Handle custom clarifications."""
        print(f"\n🔧 CUSTOM CLARIFICATION: {clarification.user_guidance}")
        if hasattr(clarification, 'custom_data'):
            print(f"Additional data: {json.dumps(clarification.custom_data, indent=2)}")
        user_input = input("Please provide your response: ")
        on_resolution(clarification, user_input)

def handle_clarifications(plan_run, portia_instance):
    """Handle any clarifications that arise during plan execution."""
    while plan_run.state == PlanRunState.NEED_CLARIFICATION:
        print(f"\n⏸️  Plan run paused - clarifications needed")
        
        clarifications = plan_run.get_outstanding_clarifications()
        print(f"Found {len(clarifications)} clarification(s) to resolve")
        
        for i, clarification in enumerate(clarifications, 1):
            print(f"\n--- Clarification {i}/{len(clarifications)} ---")
            print(f"Category: {clarification.category}")
            print(f"Step: {clarification.step}")
            
            if isinstance(clarification, ActionClarification):
                print(f"🔐 ACTION REQUIRED: {clarification.user_guidance}")
                if hasattr(clarification, 'action_url'):
                    print(f"📎 Action URL: {clarification.action_url}")
                print("Please complete the required action and then press Enter to continue...")
                input("Press Enter when ready...")
                plan_run = portia_instance.wait_for_ready(plan_run)
                
            elif isinstance(clarification, InputClarification):
                print(f"❓ INPUT NEEDED: {clarification.user_guidance}")
                if hasattr(clarification, 'argument_name'):
                    print(f"Parameter: {clarification.argument_name}")
                user_input = input("Please provide the required input: ")
                plan_run = portia_instance.resolve_clarification(clarification, user_input, plan_run)
                
            elif isinstance(clarification, MultipleChoiceClarification):
                print(f"🤔 CHOOSE AN OPTION: {clarification.user_guidance}")
                if hasattr(clarification, 'options') and clarification.options:
                    for j, option in enumerate(clarification.options, 1):
                        print(f"{j}. {option}")
                    while True:
                        try:
                            choice = int(input(f"Please select an option (1-{len(clarification.options)}): "))
                            if 1 <= choice <= len(clarification.options):
                                selected_option = clarification.options[choice - 1]
                                plan_run = portia_instance.resolve_clarification(clarification, selected_option, plan_run)
                                break
                            else:
                                print(f"Please enter a number between 1 and {len(clarification.options)}")
                        except ValueError:
                            print("Please enter a valid number")
                else:
                    user_input = input("Your choice: ")
                    plan_run = portia_instance.resolve_clarification(clarification, user_input, plan_run)
                    
            elif isinstance(clarification, ValueConfirmationClarification):
                print(f"✅ CONFIRM VALUE: {clarification.user_guidance}")
                if hasattr(clarification, 'value_to_confirm'):
                    print(f"Value to confirm: {clarification.value_to_confirm}")
                response = input("Is this correct? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    plan_run = portia_instance.resolve_clarification(clarification, True, plan_run)
                else:
                    plan_run = portia_instance.resolve_clarification(clarification, False, plan_run)
                    
            elif isinstance(clarification, CustomClarification):
                print(f"🔧 CUSTOM CLARIFICATION: {clarification.user_guidance}")
                if hasattr(clarification, 'custom_data'):
                    print(f"Additional data: {json.dumps(clarification.custom_data, indent=2)}")
                user_input = input("Please provide your response: ")
                plan_run = portia_instance.resolve_clarification(clarification, user_input, plan_run)
                
            else:
                print(f"⚠️  Unknown clarification type: {type(clarification)}")
                user_input = input("Please provide your response: ")
                plan_run = portia_instance.resolve_clarification(clarification, user_input, plan_run)
        
        if plan_run.state == PlanRunState.NEED_CLARIFICATION:
            print("\n🔄 Resuming plan run...")
            plan_run = portia_instance.resume(plan_run)
    
    return plan_run

# Core functions
def research_feature(portia: Portia, feature_request: FeatureRequest) -> FeatureAnalysis:
    """Research the feature using web search and analysis."""
    print(f"\n🔍 Researching feature: {feature_request.name}")
    
    # Create research plan
    research_plan = PlanBuilder(
        f"Research the feature '{feature_request.name}' comprehensively",
        structured_output_schema=FeatureAnalysis
    ).step(
        f"Search for information about {feature_request.name} and similar features",
        tool_id="portia:tavily::search"
    ).step(
        f"Analyze the search results and create a comprehensive analysis of {feature_request.name}",
        tool_id="llm_tool"
    ).build()
    
    print("Executing research plan...")
    research_run = portia.run_plan(research_plan)
    
    # Handle clarifications
    if research_run.state == PlanRunState.NEED_CLARIFICATION:
        print("⏸️  Clarifications needed during research...")
        research_run = handle_clarifications(research_run, portia)
    
    if research_run.state == PlanRunState.COMPLETE:
        analysis = research_run.outputs.final_output.value
        print("✅ Research completed successfully")
        return analysis
    else:
        print(f"⚠️  Research failed with state: {research_run.state}")
        raise Exception("Feature research failed")

def create_prd_in_notion(portia: Portia, analysis: FeatureAnalysis) -> str:
    """Create a PRD in Notion based on the analysis."""
    print(f"\n📝 Creating PRD in Notion for: {analysis.feature_name}")
    
    # Create PRD content
    prd_content = PRDContent(
        title=f"PRD: {analysis.feature_name}",
        executive_summary=f"Implementation of {analysis.feature_name} based on comprehensive market research and technical analysis.",
        problem_statement=analysis.description,
        solution_overview="Detailed solution based on research findings",
        user_stories=["As a user, I want..."],
        acceptance_criteria=["Feature works as expected", "Performance meets requirements"],
        technical_requirements=analysis.technical_considerations,
        design_considerations=["User experience", "Accessibility", "Performance"],
        timeline="TBD based on complexity",
        dependencies=["Technical infrastructure", "Design resources"]
    )
    
    # Create Notion page creation plan
    prd_plan = PlanBuilder(
        f"Create a PRD page in Notion for {analysis.feature_name}",
        structured_output_schema=NotionPageOutput
    ).step(
        f"Create a new page in Notion with the PRD content for {analysis.feature_name}",
        tool_id="portia:mcp:mcp.notion.com:notion_create_pages"
    ).build()
    
    print("Executing PRD creation plan...")
    prd_run = portia.run_plan(prd_plan)
    
    # Handle clarifications
    if prd_run.state == PlanRunState.NEED_CLARIFICATION:
        print("⏸️  Clarifications needed during PRD creation...")
        prd_run = handle_clarifications(prd_run, portia)
    
    if prd_run.state == PlanRunState.COMPLETE:
        page_output = prd_run.outputs.final_output.value
        print(f"✅ PRD created successfully in Notion (Page ID: {page_output.page_id})")
        return page_output.page_id
    else:
        print(f"⚠️  PRD creation failed with state: {prd_run.state}")
        raise Exception("PRD creation failed")

def create_linear_issue(portia: Portia, analysis: FeatureAnalysis) -> str:
    """Create an issue in Linear for the feature."""
    print(f"\n🎫 Creating Linear issue for: {analysis.feature_name}")
    
    # Create Linear issue creation plan using Portia cloud tools
    issue_plan = PlanBuilder(
        f"Create a Linear issue for implementing {analysis.feature_name}",
        structured_output_schema=LinearIssueOutput
    ).step(
        f"Create a new issue in Linear for {analysis.feature_name} with detailed description and requirements",
        tool_id="portia:mcp:mcp.linear.app:create_issue"
    ).build()
    
    print("Executing issue creation plan...")
    issue_run = portia.run_plan(issue_plan)
    
    # Handle clarifications
    if issue_run.state == PlanRunState.NEED_CLARIFICATION:
        print("⏸️  Clarifications needed during issue creation...")
        issue_run = handle_clarifications(issue_run, portia)
    
    if issue_run.state == PlanRunState.COMPLETE:
        issue_output = issue_run.outputs.final_output.value
        print(f"✅ Linear issue created successfully (Issue ID: {issue_output.issue_id})")
        return issue_output.issue_id
    else:
        print(f"⚠️  Issue creation failed with state: {issue_run.state}")
        raise Exception("Linear issue creation failed")

def create_linear_tasks(portia: Portia, analysis: FeatureAnalysis, issue_id: str) -> List[LinearTaskOutput]:
    """Create multiple Linear tasks (backend, frontend, testing, documentation) for a feature."""
    print(f"\n  🎯 Creating Linear tasks for issue: {issue_id}")
    
    # Define task types and their descriptions
    task_types = [
        {
            "type": "backend",
            "title": f"Backend Implementation: {analysis.feature_name}",
            "description": f"Implement the backend services and APIs for {analysis.feature_name}. "
                          f"Focus on data models, business logic, and API endpoints. "
                          f"Technical considerations: {', '.join(analysis.technical_considerations[:3])}"
        },
        {
            "type": "frontend",
            "title": f"Frontend Implementation: {analysis.feature_name}",
            "description": f"Create the user interface for {analysis.feature_name}. "
                          f"Focus on user experience, responsive design, and accessibility. "
                          f"Implementation approaches: {', '.join(analysis.implementation_approaches[:3])}"
        },
        {
            "type": "testing",
            "title": f"Testing: {analysis.feature_name}",
            "description": f"Comprehensive testing for {analysis.feature_name}. "
                          f"Unit tests, integration tests, and user acceptance testing. "
                          f"Success metrics to validate: {', '.join(analysis.success_metrics[:3])}"
        },
        {
            "type": "documentation",
            "title": f"Documentation: {analysis.feature_name}",
            "description": f"Documentation for {analysis.feature_name}. "
                          f"API documentation, user guides, and technical specifications. "
                          f"Key insights: {', '.join([source.key_insights[0] for source in analysis.research_sources[:2] if source.key_insights])}"
        }
    ]
    
    created_tasks = []
    
    for task_info in task_types:
        print(f"    📝 Creating {task_info['type']} task...")
        
        # Create task plan
        task_plan = PlanBuilder(
            f"Create {task_info['type']} task for {analysis.feature_name}",
            structured_output_schema=LinearTaskOutput
        ).step(
            f"Create a new {task_info['type']} task in Linear. "
            f"Title: {task_info['title']}. "
            f"Description: {task_info['description']}. "
            f"This should be a standalone task (not linked to parent issue). "
            f"Use the default team or ask for team selection if needed.",
            tool_id="portia:mcp:mcp.linear.app:create_issue"
        ).build()
        
        task_run = portia.run_plan(task_plan)
        
        # Handle clarifications
        if task_run.state == PlanRunState.NEED_CLARIFICATION:
            print(f"      ⏸️  Clarifications needed for {task_info['type']} task...")
            task_run = handle_clarifications(task_run, portia)
        
        if task_run.state == PlanRunState.COMPLETE:
            task_output = task_run.outputs.final_output.value
            created_tasks.append(task_output)
            print(f"    ✅ {task_info['type'].title()} task created: {task_output.task_id}")
        else:
            print(f"    ⚠️  {task_info['type'].title()} task creation failed with state: {task_run.state}")
    
    return created_tasks

def monitor_linear_comments(portia: Portia, issue_id: str) -> List[Dict[str, Any]]:
    """Monitor comments on a Linear issue and return them."""
    print(f"\n🔍 Monitoring comments for Linear issue: {issue_id}")
    
    # Try different issue ID formats (UUID and PRA format)
    issue_formats = [issue_id]
    
    # If it's already PRA format, try that
    if issue_id.startswith('PRA-'):
        print(f"  🔍 Issue ID is PRA format: {issue_id}")
    
    for current_issue_id in issue_formats:
        try:
            print(f"\n  🔍 Fetching comments for issue: {current_issue_id}")
            
            # Try different approaches to get comments
            print("    📝 Attempting to fetch comments...")
            
            comments_plan = PlanBuilder(
                f"List comments for Linear issue {current_issue_id}",
                structured_output_schema=LinearCommentsListOutput
            ).step(
                f"Get all comments for the Linear issue with ID {current_issue_id}. "
                f"If this is a PRA-8 issue, make sure to fetch all comments including any that might be in the description or comments section.",
                tool_id="portia:mcp:mcp.linear.app:list_comments"
            ).build()
            
            comments_run = portia.run_plan(comments_plan)
            
            # Handle clarifications
            if comments_run.state == PlanRunState.NEED_CLARIFICATION:
                print("    ⏸️  Clarifications needed for fetching comments...")
                comments_run = handle_clarifications(comments_run, portia)
            
            if comments_run.state == PlanRunState.COMPLETE:
                comments_output = comments_run.outputs.final_output.value
                print(f"    ✅ Found comments response: {comments_output}")
                
                # Debug: Show the exact structure
                print(f"    🔍 Response type: {type(comments_output)}")
                
                # Parse the actual comments from the Linear response
                comments_data = []
                
                # Handle both string and object responses
                if isinstance(comments_output, str):
                    # Response is a JSON string, parse it
                    try:
                        import json
                        parsed_response = json.loads(comments_output)
                        print(f"    🔍 Parsed response: {parsed_response}")
                        
                        # Extract comments from the parsed response
                        if isinstance(parsed_response, dict) and 'content' in parsed_response:
                            content = parsed_response['content']
                            if isinstance(content, list) and len(content) > 0:
                                # Comments are in content[0].text as a JSON string
                                if 'text' in content[0]:
                                    try:
                                        raw_comments = json.loads(content[0]['text'])
                                        print(f"    📝 Raw comments from Linear: {raw_comments}")
                                        
                                        if isinstance(raw_comments, list):
                                            comments_data = raw_comments
                                            print(f"    📝 Parsed {len(comments_data)} comments from Linear")
                                        else:
                                            print(f"    ⚠️  Unexpected comments format: {type(raw_comments)}")
                                            
                                    except json.JSONDecodeError as e:
                                        print(f"    ⚠️  Could not parse comments content as JSON: {e}")
                                        print(f"    📝 Raw text content: {content[0]['text']}")
                                        comments_data = []
                                    except Exception as e:
                                        print(f"    ⚠️  Error parsing comments: {e}")
                                        comments_data = []
                                else:
                                    print(f"    ⚠️  No 'text' field in content[0]: {content[0]}")
                            else:
                                print(f"    ⚠️  Unexpected content structure: {content}")
                        else:
                            print(f"    ⚠️  No 'content' field in response: {parsed_response}")
                            
                    except json.JSONDecodeError as e:
                        print(f"    ⚠️  Could not parse response as JSON: {e}")
                        comments_data = []
                    except Exception as e:
                        print(f"    ⚠️  Error parsing response: {e}")
                        comments_data = []
                        
                elif hasattr(comments_output, 'content') and comments_output.content:
                    # Response is a structured object (our expected case)
                    print(f"    🔍 Response attributes: {dir(comments_output)}")
                    print(f"    🔍 Content type: {type(comments_output.content)}")
                    print(f"    🔍 Content length: {len(comments_output.content) if hasattr(comments_output.content, '__len__') else 'N/A'}")
                    
                    if hasattr(comments_output.content, '__len__') and len(comments_output.content) > 0:
                        print(f"    🔍 Content[0] type: {type(comments_output.content[0])}")
                        print(f"    🔍 Content[0] attributes: {dir(comments_output.content[0])}")
                        if hasattr(comments_output.content[0], 'text'):
                            print(f"    🔍 Content[0].text: {comments_output.content[0].text}")
                            print(f"    🔍 Content[0].text type: {type(comments_output.content[0].text)}")
                    
                    # Linear returns comments in content[0].text as a JSON string
                    if len(comments_output.content) > 0 and hasattr(comments_output.content[0], 'text'):
                        try:
                            import json
                            # Parse the text field which contains the actual comments as JSON
                            raw_comments = json.loads(comments_output.content[0].text)
                            print(f"    📝 Raw comments from Linear: {raw_comments}")
                            
                            # If raw_comments is a list, use it directly
                            if isinstance(raw_comments, list):
                                comments_data = raw_comments
                                print(f"    📝 Parsed {len(comments_data)} comments from Linear")
                            else:
                                print(f"    ⚠️  Unexpected comments format: {type(raw_comments)}")
                                
                        except json.JSONDecodeError as e:
                            print(f"    ⚠️  Could not parse comments content as JSON: {e}")
                            print(f"    📝 Raw text content: {comments_output.content[0].text}")
                            comments_data = []
                        except Exception as e:
                            print(f"    ⚠️  Error parsing comments: {e}")
                            comments_data = []
                    else:
                        print(f"    ⚠️  Unexpected content structure: {comments_output.content}")
                else:
                    print(f"    📝 No content found in response")
                
                return comments_data
                    
            else:
                print(f"    ⚠️  Failed to fetch comments with state: {comments_run.state}")
                
        except Exception as e:
            print(f"    ⚠️  Comment monitoring failed for {current_issue_id}: {e}")

    return []

def create_new_comment(portia: Portia, issue_id: str, title: str, content: str) -> Dict[str, Any]:
    """Create a new comment on a Linear issue."""
    try:
        print(f"\n  💬 Creating new comment for issue: {issue_id}")
        
        if not content:
            raise ValueError("Comment content cannot be empty")
        
        # Create the comment
        comment_plan = PlanBuilder(
            f"Create a new comment on Linear issue {issue_id}",
            structured_output_schema=LinearCommentOutput
        ).step(
            f"Create a new comment on Linear issue {issue_id}. "
            f"Title: {title if title else 'No title'}. "
            f"Content: {content}",
            tool_id="portia:mcp:mcp.linear.app:create_comment"
        ).build()
        
        comment_run = portia.run_plan(comment_plan)
        
        # Handle clarifications
        if comment_run.state == PlanRunState.NEED_CLARIFICATION:
            print("    ⏸️  Clarifications needed for comment creation...")
            comment_run = handle_clarifications(comment_run, portia)
        
        if comment_run.state == PlanRunState.COMPLETE:
            comment_output = comment_run.outputs.final_output.value
            print(f"    ✅ New comment created successfully")
            return {"success": True, "comment_id": comment_output.comment_id, "message": "Comment created successfully"}
            
        else:
            print(f"    ⚠️  Comment creation failed with state: {comment_run.state}")
            return {"success": False, "message": f"Comment creation failed with state: {comment_run.state}"}
            
    except Exception as e:
        print(f"    ⚠️  Failed to create new comment: {e}")
        return {"success": False, "message": f"Failed to create comment: {str(e)}"}

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Feature Research Agent API",
        "version": "1.0.0",
        "endpoints": {
            "POST /research": "Start feature research workflow",
            "GET /research/{session_id}": "Get research session status",
            "POST /comments": "Create a new comment on Linear issue",
            "GET /comments/{issue_id}": "Get comments for a Linear issue"
        }
    }

@app.post("/research", response_model=ResearchSessionResponse)
async def start_research(feature_request: FeatureRequest, background_tasks: BackgroundTasks):
    """Start a feature research workflow."""
    try:
        # Generate unique session ID
        session_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{feature_request.name.replace(' ', '_')}"
        
        # Initialize session
        research_sessions[session_id] = {
            "status": "initializing",
            "progress": 0,
            "result": None,
            "error": None
        }
        
        # Start background research task
        background_tasks.add_task(
            run_research_workflow,
            session_id,
            feature_request
        )
        
        return ResearchSessionResponse(
            session_id=session_id,
            status="started",
            progress=0,
            result=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")

@app.get("/research/{session_id}", response_model=ResearchSessionResponse)
async def get_research_status(session_id: str):
    """Get the status of a research session."""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Research session not found")
    
    session = research_sessions[session_id]
    return ResearchSessionResponse(
        session_id=session_id,
        status=session["status"],
        progress=session["progress"],
        result=session["result"],
        error=session["error"]
    )

@app.post("/comments", response_model=CommentResponse)
async def create_comment(comment_request: CommentRequest):
    """Create a new comment on a Linear issue."""
    try:
        # Set up Portia with cloud tools
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)
        os.environ['PORTIA_API_KEY'] = portia_api_key
        
        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=PortiaToolRegistry(config)
        )
        
        # Create the comment
        result = create_new_comment(
            portia, 
            comment_request.issue_id, 
            comment_request.title, 
            comment_request.content
        )
        
        if result["success"]:
            return CommentResponse(
                success=True,
                message=result["message"],
                data={"comment_id": result["comment_id"]}
            )
        else:
            return CommentResponse(
                success=False,
                message=result["message"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")

@app.get("/comments/{issue_id}")
async def get_comments(issue_id: str):
    """Get comments for a Linear issue."""
    try:
        # Set up Portia with cloud tools
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)
        os.environ['PORTIA_API_KEY'] = portia_api_key
        
        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=PortiaToolRegistry(config)
        )
        
        # Get comments
        comments = monitor_linear_comments(portia, issue_id)
        
        return {
            "issue_id": issue_id,
            "comments": comments,
            "count": len(comments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {str(e)}")

async def run_research_workflow(session_id: str, feature_request: FeatureRequest):
    """Run the complete research workflow in the background."""
    try:
        # Update session status
        research_sessions[session_id]["status"] = "setting_up"
        research_sessions[session_id]["progress"] = 10
        
        # Set up Portia with cloud tools
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)
        os.environ['PORTIA_API_KEY'] = portia_api_key
        
        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=PortiaToolRegistry(config)
        )
        
        # Update session status
        research_sessions[session_id]["status"] = "researching"
        research_sessions[session_id]["progress"] = 30
        
        # Research the feature
        analysis = research_feature(portia, feature_request)
        
        # Update session status
        research_sessions[session_id]["status"] = "creating_prd"
        research_sessions[session_id]["progress"] = 60
        
        # Create PRD in Notion (if available)
        notion_page_id = None
        if os.getenv('NOTION_API_KEY'):
            try:
                notion_page_id = create_prd_in_notion(portia, analysis)
            except Exception as e:
                print(f"⚠️  Notion PRD creation failed: {e}")
        
        # Update session status
        research_sessions[session_id]["status"] = "creating_linear_issue"
        research_sessions[session_id]["progress"] = 80
        
        # Create Linear issue using Portia cloud tools
        linear_issue_id = None
        try:
            linear_issue_id = create_linear_issue(portia, analysis)
        except Exception as e:
            print(f"⚠️  Linear issue creation failed: {e}")
            print("This may be due to authentication or permission issues")
        
        # Create Linear tasks for the issue
        if linear_issue_id:
            try:
                create_linear_tasks(portia, analysis, linear_issue_id)
            except Exception as e:
                print(f"⚠️  Linear task creation failed: {e}")
                print("This may be due to tool response format or permissions")
        
        # Update session status
        research_sessions[session_id]["status"] = "completed"
        research_sessions[session_id]["progress"] = 100
        research_sessions[session_id]["result"] = {
            "feature_name": analysis.feature_name,
            "analysis": analysis.model_dump(),
            "notion_page_id": notion_page_id,
            "linear_issue_id": linear_issue_id
        }
        
        print(f"🎉 Research workflow completed for session: {session_id}")
        
    except Exception as e:
        research_sessions[session_id]["status"] = "failed"
        research_sessions[session_id]["error"] = str(e)
        print(f"❌ Research workflow failed for session {session_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Feature Research Agent API Server...")
    print(f"🔑 Using Portia API key: {portia_api_key[:8]}...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
