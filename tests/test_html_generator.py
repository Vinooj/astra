import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples/research_workflows'))
import pytest
import asyncio
import re
import json
from unittest.mock import MagicMock

from astra_framework.core.state import SessionState
from html_generator import HtmlGenerator
from models import Article, FinalReport, Editorial, Newsletter

@pytest.fixture
def sample_editorial():
    article1 = Article(
        url="http://example.com/article1",
        title="Article One",
        content="Content of article one.",
        published_date="2023-01-01",
        summary="Summary of article one."
    )
    article2 = Article(
        url="http://example.com/article2",
        title="Article Two",
        content="Content of article two.",
        published_date="2023-01-02",
        summary="Summary of article two."
    )
    article3 = Article(
        url="http://example.com/article3",
        title="Article Three",
        content="Content of article three.",
        published_date="2023-01-03",
        summary="Summary of article three."
    )

    report1 = FinalReport(
        editorial="Topic A Editorial",
        articles=[article1],
        approved=True,
        feedback="",
        topic_name="Topic A"
    )
    report2 = FinalReport(
        editorial="Topic B Editorial",
        articles=[article2, article3],
        approved=False,
        feedback="Needs more sources.",
        topic_name="Topic B"
    )

    editorial = Editorial(
        main_title="Weekly Oncology Newsletter",
        editorial_content="This week's highlights in oncology research.",
        final_report=[report1, report2]
    )
    return editorial

@pytest.mark.asyncio
async def test_html_generator_generates_html(sample_editorial):
    html_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples/research_workflows/newsletter_template.html')
    agent = HtmlGenerator(
        agent_name="TestHtmlGenerator",
        html_template_path=html_template_path
    )

    state = SessionState(session_id="test_session")
    state.data["editorial"] = sample_editorial

    result_state = await agent.execute(state)

    assert isinstance(result_state.final_content, Newsletter)
    html_content = result_state.final_content.html_content

    # Save the generated HTML to a file for inspection
    with open("tests/test_newsletter_output.html", "w") as f:
        f.write(html_content)

    # Normalize whitespace for robust comparison
    normalized_html_content = re.sub(r'\s+', ' ', html_content).strip()

    print("--- FULL GENERATED HTML CONTENT (NORMALIZED) ---")
    print(normalized_html_content)
    print("--- END FULL GENERATED HTML CONTENT (NORMALIZED) ---")

    # Check main title and editorial content
    assert sample_editorial.main_title in normalized_html_content
    assert sample_editorial.editorial_content in normalized_html_content

    # Check TOC items
    assert normalized_html_content.find('<li><a href="#topic-a">Topic A</a></li>') != -1
    assert normalized_html_content.find('<li><a href="#topic-b">Topic B</a></li>') != -1

    # Check topic sections and reports
    assert normalized_html_content.find('<div class="topic-section" id="topic-a">') != -1
    assert normalized_html_content.find('<h2>Topic A</h2>') != -1
    assert normalized_html_content.find('<div class="topic-section" id="topic-b">') != -1
    assert normalized_html_content.find('<h2>Topic B</h2>') != -1

    # Check report details
    assert normalized_html_content.find('<h3>Topic A Editorial</h3>') != -1
    assert normalized_html_content.find('Approved') != -1
    assert normalized_html_content.find('<h3>Topic B Editorial</h3>') != -1
    assert normalized_html_content.find('Feedback: Needs more sources.') != -1

    # Check article details
    assert normalized_html_content.find('<a href="http://example.com/article1" target="_blank">Article One</a>') != -1
    assert normalized_html_content.find('Summary of article one.') != -1
    assert normalized_html_content.find('<strong>Published:</strong> 2023-01-01') != -1

    assert normalized_html_content.find('<a href="http://example.com/article2" target="_blank">Article Two</a>') != -1
    assert normalized_html_content.find('Summary of article two.') != -1
    assert normalized_html_content.find('<strong>Published:</strong> 2023-01-02') != -1

    assert normalized_html_content.find('<a href="http://example.com/article3" target="_blank">Article Three</a>') != -1
    assert normalized_html_content.find('Summary of article three.') != -1
    assert normalized_html_content.find('<strong>Published:</strong> 2023-01-03') != -1

@pytest.mark.asyncio
async def test_html_generator_no_editorial_data():
    html_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples/research_workflows/newsletter_template.html')
    agent = HtmlGenerator(
        agent_name="TestHtmlGenerator",
        html_template_path=html_template_path
    )
    state = SessionState(session_id="test_session")

    with pytest.raises(ValueError, match="Editorial data not found in session state."):
        await agent.execute(state)

@pytest.mark.asyncio
async def test_html_generator_from_json_input():
    # Load the editorial data from the JSON file
    with open("tests/editorial_output.json", "r") as f:
        editorial_json_data = f.read()
    
    editorial = Editorial.model_validate_json(editorial_json_data)

    html_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples/research_workflows/newsletter_template.html')
    agent = HtmlGenerator(
        agent_name="TestHtmlGeneratorFromJson",
        html_template_path=html_template_path
    )

    state = SessionState(session_id="test_session_from_json")
    state.data["editorial"] = editorial

    result_state = await agent.execute(state)

    assert isinstance(result_state.final_content, Newsletter)
    html_content = result_state.final_content.html_content

    # Save the generated HTML to a file for inspection
    with open("tests/generated_from_json_newsletter.html", "w") as f:
        f.write(html_content)

    # Basic assertion to ensure content is generated
    assert len(html_content) > 0
    assert editorial.main_title in html_content
    assert editorial.editorial_content in html_content
