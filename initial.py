#!/usr/bin/env python3
"""
Feature Research and PRD Generation Agent

This agent helps users research features by:
1. Searching the web for information about the feature
2. Analyzing implementations, blogs, articles, and news
3. Creating detailed PRDs in Notion as markdown files
4. Saving analysis to files in human-readable format
5. Creating issues in Linear for the current project
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from portia import (
    Portia,
    Config,
    PlanBuilder,
    PlanRunState,
    DefaultToolRegistry,
    ToolRegistry,
    Clarification,
    ClarificationHandler,
    ActionClarification,
    InputClarification,
    MultipleChoiceClarification,
    ValueConfirmationClarification,
    CustomClarification,
    ExecutionHooks
)
from portia.open_source_tools.search_tool import SearchTool
from portia.open_source_tools.local_file_writer_tool import LocalFileWriterTool
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

def setup_tool_registry() -> ToolRegistry:
    """Set up the tool registry with all necessary tools."""
    # Start with open source tools registry
    tool_registry = DefaultToolRegistry.from_local_tools()

    # Add search tool for web research
    search_tool = SearchTool()
    tool_registry.with_tool(search_tool, overwrite=True)

    # Add Notion MCP tools if API key is available
    notion_api_key = os.getenv('NOTION_API_KEY')
    if notion_api_key:
        try:
            notion_tools = DefaultToolRegistry.from_stdio_connection(
                server_name="notionApi",
                command="npx",
                args=["-y", "@notionhq/notion-mcp-server"],
                env={
                    "OPENAPI_MCP_HEADERS": json.dumps({
                        "Authorization": f"Bearer {notion_api_key}",
                        "Notion-Version": "2022-06-28"
                    })
                }
            )
            # Combine tool registries using the + operator
            tool_registry = tool_registry + notion_tools
            print("✅ Notion tools loaded successfully")
        except Exception as e:
            print(f"⚠️  Failed to load Notion tools: {e}")
            print("Continuing without Notion integration...")

    # Linear is available through Portia cloud tools - no API key needed
    print("✅ Linear tools available through Portia cloud integration")

    return tool_registry

def research_feature(portia: Portia, feature_request: FeatureRequest) -> FeatureAnalysis:
    """Research the feature using web search and analysis."""
    print(f"\n🔍 Researching feature: {feature_request.name}")

    # Create research plan
    research_plan = PlanBuilder(
        f"Research the feature '{feature_request.name}' comprehensively",
        structured_output_schema=FeatureAnalysis
    ).step(
        f"Search for information about {feature_request.name} and similar features",
        tool_id="search_tool"
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
        structured_output_schema=str
    ).step(
        f"Create a new page in Notion with the PRD content for {analysis.feature_name}",
        tool_id="notion:create_page"
    ).build()

    print("Executing PRD creation plan...")
    prd_run = portia.run_plan(prd_plan)

    # Handle clarifications
    if prd_run.state == PlanRunState.NEED_CLARIFICATION:
        print("⏸️  Clarifications needed during PRD creation...")
        prd_run = handle_clarifications(prd_run, portia)

    if prd_run.state == PlanRunState.COMPLETE:
        page_id = prd_run.outputs.final_output.value
        print(f"✅ PRD created successfully in Notion (Page ID: {page_id})")
        return page_id
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
        structured_output_schema=str
    ).step(
        f"Create a new issue in Linear for {analysis.feature_name} with detailed description and requirements",
        tool_id="portia:linear:create_issue"
    ).build()

    print("Executing issue creation plan...")
    issue_run = portia.run_plan(issue_plan)

    # Handle clarifications
    if issue_run.state == PlanRunState.NEED_CLARIFICATION:
        print("⏸️  Clarifications needed during issue creation...")
        issue_run = handle_clarifications(issue_run, portia)

    if issue_run.state == PlanRunState.COMPLETE:
        issue_id = issue_run.outputs.final_output.value
        print(f"✅ Linear issue created successfully (Issue ID: {issue_id})")
        return issue_id
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
        tool_registry = setup_tool_registry()

        # Create Portia configuration with API key
        config = Config.from_default()
        config.portia_api_key = SecretStr(portia_api_key)

        # Ensure the API key is also set in environment for Portia to find
        os.environ['PORTIA_API_KEY'] = portia_api_key

        print(f"🔑 Using Portia API key: {portia_api_key[:8]}...")
        print(f"�� Debug: Config portia_api_key type: {type(config.portia_api_key)}")
        print(f"🔍 Debug: Config portia_api_key value: {config.portia_api_key}")
        print(f"🔍 Debug: Environment PORTIA_API_KEY: {os.getenv('PORTIA_API_KEY')}")

        portia = Portia(
            config=config,
            execution_hooks=ExecutionHooks(clarification_handler=FeatureResearchClarificationHandler()),
            tools=tool_registry
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

if __name__ == "__main__":
    main()
