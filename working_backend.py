#!/usr/bin/env python3
"""
Feature Research and PRD Generation Agent

This agent helps users research features by:
1. Searching the web for information about the feature
2. Analyzing implementations, blogs, articles, and news
3. Creating detailed PRDs in Notion
4. Saving analysis to files
5. Creating issues in Linear for the current project
"""

import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Callable
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
from pydantic import SecretStr
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Check for required environment variables
portia_api_key = os.getenv('PORTIA_API_KEY')
if not portia_api_key:
    print("❌ Error: PORTIA_API_KEY environment variable is required")
    print("Please set PORTIA_API_KEY in your .env file")
    print("You can get your API key from: https://app.portialabs.ai > API Keys")
    exit(1)

# Debug: Log the API key (first 8 chars for security)
print(f"🔍 Debug: Found PORTIA_API_KEY: {portia_api_key[:8]}... (length: {len(portia_api_key)})")
print(f"🔍 Debug: Full API key: {portia_api_key}")

# Set the environment variable explicitly to ensure it's available
os.environ['PORTIA_API_KEY'] = portia_api_key

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

def get_user_feature_request() -> FeatureRequest:
    """Get feature request from user input."""
    print("🎯 Feature Research and PRD Generation Agent")
    print("=" * 50)
    print("I'll help you research a feature, create a detailed PRD, and set up project issues.")
    print()
    
    feature_name = input("What feature would you like to research? ").strip()
    feature_description = input("Please describe the feature in detail: ").strip()
    
    return FeatureRequest(name=feature_name, description=feature_description)

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

def save_analysis_to_file(analysis: FeatureAnalysis) -> str:
    """Save the analysis to a local file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feature_analysis_{analysis.feature_name.replace(' ', '_')}_{timestamp}.json"
    
    # Convert to dict for JSON serialization
    analysis_dict = analysis.model_dump()
    
    with open(filename, 'w') as f:
        json.dump(analysis_dict, f, indent=2)
    
    print(f"💾 Analysis saved to: {filename}")
    return filename

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

def main():
    """Main function to run the feature research agent."""
    try:
        # Get feature request from user
        feature_request = get_user_feature_request()
        
        # Set up Portia with tools
        print("\n🔧 Setting up tools...")
        
        # Create Portia configuration with API key
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)
        
        # Ensure the API key is also set in environment for Portia to find
        os.environ['PORTIA_API_KEY'] = portia_api_key
        
        print(f"🔑 Using Portia API key: {portia_api_key[:8]}...")
        print(f"🔍 Debug: Config portia_api_key type: {type(config.portia_api_key)}")
        print(f"🔍 Debug: Config portia_api_key value: {config.portia_api_key}")
        print(f"🔍 Debug: Environment PORTIA_API_KEY: {os.getenv('PORTIA_API_KEY')}")
        
        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=PortiaToolRegistry(config)
        )
        
        # Research the feature
        analysis = research_feature(portia, feature_request)
        
        # Save analysis to file
        analysis_file = save_analysis_to_file(analysis)
        
        # Create PRD in Notion (if available)
        notion_page_id = None
        if os.getenv('NOTION_API_KEY'):
            try:
                notion_page_id = create_prd_in_notion(portia, analysis)
            except Exception as e:
                print(f"⚠️  Notion PRD creation failed: {e}")
        
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
        
        # Monitor comments for the Linear issue
        if linear_issue_id:
            try:
                monitor_linear_comments(portia, linear_issue_id)
            except Exception as e:
                print(f"⚠️  Linear comment monitoring failed: {e}")
                print("This may be due to tool response format or permissions")
        
        # Summary
        print(f"\n🎉 Feature Research Complete!")
        print("=" * 50)
        print(f"Feature: {analysis.feature_name}")
        print(f"Analysis saved to: {analysis_file}")
        if notion_page_id:
            print(f"PRD created in Notion: {notion_page_id}")
        if linear_issue_id:
            print(f"Linear issue created: {linear_issue_id}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Feature research interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during feature research: {str(e)}")
    finally:
        print("\n🏁 Feature research session completed")

# Additional schemas for Linear operations
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

def monitor_linear_comments(portia: Portia, issue_id: str) -> None:
    """Monitor comments on a Linear issue and process them with user validation."""
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
                
                # Process the comments if we have any
                if comments_data and len(comments_data) > 0:
                    print(f"  📝 Processing {len(comments_data)} comments...")
                    
                    # Ask user if they want to process comments
                    user_input = input("\n💭 Do you want to process and validate comments for this issue? (y/n): ").lower().strip()
                    
                    if user_input in ['y', 'yes']:
                        process_comments_with_user(portia, current_issue_id, comments_data)
                    else:
                        print("  ⏭️  Skipping comment processing")
                
                # Always offer the option to create a new comment
                print(f"\n💬 Comment Management Options:")
                print(f"  1. Process existing comments")
                print(f"  2. Create a new comment")
                print(f"  3. Skip comment management")
                
                choice = input("\n💭 What would you like to do? (1/2/3): ").strip()
                
                if choice == "1" and comments_data and len(comments_data) > 0:
                    # Process existing comments
                    process_comments_with_user(portia, current_issue_id, comments_data)
                elif choice == "2":
                    # Create a new comment
                    create_new_comment(portia, current_issue_id)
                elif choice == "3":
                    print("  ⏭️  Skipping comment management")
                else:
                    print("  ⚠️  Invalid choice or no existing comments to process")
                    if choice == "1":
                        print("  💡 No existing comments found, but you can still create a new one")
                        create_new_comment(portia, current_issue_id)
                    return  # Exit after handling the choice
                    
            else:
                print("  📝 No comments found for this issue")
                
                # Offer to create a new comment even when there are no existing ones
                print(f"\n💬 No existing comments found. Would you like to create a new comment?")
                user_input = input("💭 Create a new comment? (y/n): ").lower().strip()
                
                if user_input in ['y', 'yes']:
                    create_new_comment(portia, current_issue_id)
                else:
                    print("  ⏭️  Skipping comment creation")
                    
        except Exception as e:
            print(f"    ⚠️  Comment monitoring failed for {current_issue_id}: {e}")

    print(f"\n  💡 Since no comments were found, here are some things to check:")
    print(f"    1. Make sure the issue ID is correct: {issue_id}")
    print(f"    2. Try using the PRA-8 format instead of the UUID")
    print(f"    3. Check if the Linear tool has the right permissions")
    print(f"    4. Verify that comments exist in the Linear interface")

def create_new_comment(portia: Portia, issue_id: str) -> None:
    """Create a new comment on a Linear issue."""
    try:
        print(f"\n  💬 Creating new comment for issue: {issue_id}")
        
        # Get comment content from user
        comment_title = input("  📝 Comment title (optional): ").strip()
        comment_body = input("  📝 Comment content: ").strip()
        
        if not comment_body:
            print("  ⚠️  Comment content cannot be empty")
            return
        
        # Create the comment
        comment_plan = PlanBuilder(
            f"Create a new comment on Linear issue {issue_id}",
            structured_output_schema=LinearCommentOutput
        ).step(
            f"Create a new comment on Linear issue {issue_id}. "
            f"Title: {comment_title if comment_title else 'No title'}. "
            f"Content: {comment_body}",
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
            
            # Debug: Show what was returned
            print(f"    🔍 Comment response: {comment_output}")
            print(f"    🔍 Comment response type: {type(comment_output)}")
            
        else:
            print(f"    ⚠️  Comment creation failed with state: {comment_run.state}")
            
    except Exception as e:
        print(f"    ⚠️  Failed to create new comment: {e}")
        print(f"    💡 This might be due to tool response format or permissions")

def process_comments_with_user(portia: Portia, issue_id: str, comments_data: List[dict]) -> None:
    """Process comments with user validation and take appropriate actions."""
    print(f"\n  🔍 Processing comments for issue: {issue_id}")
    
    for comment in comments_data:
        # Extract author name from the nested structure
        author_name = "Unknown"
        if 'author' in comment and isinstance(comment['author'], dict):
            author_name = comment['author'].get('name', 'Unknown')
        elif 'author' in comment:
            author_name = str(comment['author'])
        
        # Extract comment body
        comment_body = comment.get('body', 'No content')
        
        print(f"\n    💬 Comment from {author_name}:")
        print(f"       {comment_body}")
        
        # Ask user if this comment is valid
        user_input = input(f"    ✅ Is this comment valid and actionable? (y/n): ").lower().strip()
        
        if user_input in ['y', 'yes']:
            print(f"    🔄 Refining issue based on valid comment...")
            refine_issue_from_comment(portia, issue_id, comment)
        else:
            print(f"    ❌ Comment marked as invalid. Getting feedback...")
            feedback = input(f"    💭 Why is this comment not a valid blocker? Provide feedback: ").strip()
            if feedback:
                create_feedback_comment(portia, issue_id, comment, feedback)
            else:
                print(f"    ⏭️  No feedback provided, skipping...")

def refine_issue_from_comment(portia: Portia, issue_id: str, comment: dict) -> None:
    """Refine a Linear issue based on a valid comment."""
    try:
        print(f"    🔄 Updating issue {issue_id} based on comment...")
        
        # Create update plan
        update_plan = PlanBuilder(
            f"Update Linear issue {issue_id} based on comment feedback",
            structured_output_schema=LinearCommentOutput
        ).step(
            f"Update the Linear issue {issue_id} to incorporate the feedback from the comment: {comment.get('body', 'Unknown comment')}. "
            f"Refine the issue description, requirements, or acceptance criteria based on this valid feedback.",
            tool_id="portia:mcp:mcp.linear.app:update_issue"
        ).build()
        
        update_run = portia.run_plan(update_plan)
        
        # Handle clarifications
        if update_run.state == PlanRunState.NEED_CLARIFICATION:
            print(f"      ⏸️  Clarifications needed for issue update...")
            update_run = handle_clarifications(update_run, portia)
        
        if update_run.state == PlanRunState.COMPLETE:
            update_output = update_run.outputs.final_output.value
            print(f"    ✅ Issue updated successfully based on comment")
            
            # Debug: Show what was returned
            print(f"    🔍 Update response: {update_output}")
            print(f"    🔍 Update response type: {type(update_output)}")
            
        else:
            print(f"    ⚠️  Issue update failed with state: {update_run.state}")
            
    except Exception as e:
        print(f"    ⚠️  Failed to update issue: {e}")

def create_feedback_comment(portia: Portia, issue_id: str, comment: dict, feedback: str) -> None:
    """Create a feedback comment explaining why a comment is not a valid blocker."""
    try:
        print(f"    💬 Creating feedback comment...")
        
        # Create feedback comment plan
        feedback_plan = PlanBuilder(
            f"Create feedback comment on Linear issue {issue_id}",
            structured_output_schema=LinearCommentOutput
        ).step(
            f"Create a new comment on Linear issue {issue_id} explaining why the comment from {comment.get('author', {}).get('name', 'Unknown')} "
            f"is not a valid blocker. The feedback is: {feedback}. "
            f"This should be constructive and help guide future discussions.",
            tool_id="portia:mcp:mcp.linear.app:create_comment"
        ).build()
        
        feedback_run = portia.run_plan(feedback_plan)
        
        # Handle clarifications
        if feedback_run.state == PlanRunState.NEED_CLARIFICATION:
            print(f"      ⏸️  Clarifications needed for feedback comment...")
            feedback_run = handle_clarifications(feedback_run, portia)
        
        if feedback_run.state == PlanRunState.COMPLETE:
            feedback_output = feedback_run.outputs.final_output.value
            print(f"    ✅ Feedback comment created successfully")
            
            # Debug: Show what was returned
            print(f"    🔍 Feedback response: {feedback_output}")
            print(f"    🔍 Feedback response type: {type(feedback_output)}")
            
        else:
            print(f"    ⚠️  Feedback comment creation failed with state: {feedback_run.state}")
            
    except Exception as e:
        print(f"    ⚠️  Failed to create feedback comment: {e}")

def check_linear_comments_for_issue(issue_id: str) -> None:
    """Check comments for a specific Linear issue - entry point for --check-comments flag."""
    try:
        print(f"🔍 Checking comments for Linear issue: {issue_id}")
        
        # Set up Portia with cloud tools
        print("\n🔧 Setting up Portia with cloud tools...")
        
        # Create Portia configuration with API key
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)
        
        # Ensure the API key is also set in environment for Portia to find
        os.environ['PORTIA_API_KEY'] = portia_api_key
        
        print(f"🔑 Using Portia API key: {portia_api_key[:8]}...")
        
        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=PortiaToolRegistry(config)
        )
        
        # Monitor comments for the issue
        monitor_linear_comments(portia, issue_id)
        
    except Exception as e:
        print(f"❌ Error checking Linear comments: {e}")
        print("This may be due to authentication or permission issues")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Feature Research and PRD Generation Agent")
    parser.add_argument("--check-comments", type=str, help="Check comments for a specific Linear issue ID")
    
    args = parser.parse_args()
    
    if args.check_comments:
        # Run comment monitoring for a specific issue
        check_linear_comments_for_issue(args.check_comments)
    else:
        # Run the full feature research workflow
        main()
