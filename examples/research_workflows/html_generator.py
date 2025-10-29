from typing import List
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
from models import Article, FinalReport, Editorial, Newsletter

class HtmlGenerator(BaseAgent):

    def __init__(self, agent_name: str, html_template_path: str):
        super().__init__(agent_name=agent_name)
        self.html_template_path = html_template_path

    async def execute(self, state: SessionState) -> SessionState:
        editorial: Editorial = state.data.get("editorial")

        if not editorial:
            raise ValueError("Editorial data not found in session state.")

        with open(self.html_template_path, 'r') as f:
            html_template = f.read()

        reports_html = ""
        toc_items = ""
        
        # Group reports by topic name
        reports_by_topic = {}
        for report in editorial.final_report:
            if report.topic_name not in reports_by_topic:
                reports_by_topic[report.topic_name] = []
            reports_by_topic[report.topic_name].append(report)

        for topic_name, reports in reports_by_topic.items():
            topic_id = topic_name.replace(" ", "-").lower()
            toc_items += f'<li><a href="#{topic_id}">{topic_name}</a></li>'
            reports_html += f'''<div class="topic-section" id="{topic_id}">
<h2>{topic_name}</h2>
'''

            for i, report in enumerate(reports):
                report_id = f"report-{topic_id}-{i}"
                
                articles_html = ""
                for article in report.articles:
                    articles_html += f"""
                    <div class="article">
                        <h3><a href="{article.url}" target="_blank">{article.title}</a></h3>
                        <p><strong>Published:</strong> {article.published_date if article.published_date else 'N/A'}</p>
                        <p>{article.summary if article.summary else article.content}</p>
                    </div>
                    """
                
                status_class = "approved" if report.approved else "feedback"
                status_text = "Approved" if report.approved else f"Feedback: {report.feedback}"

                reports_html += f"""
                <div class="report" id="{report_id}">
                    <h3>{report.editorial}</h3>
                    <p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>
                    <div class="articles-container">
                        <h4>Articles:</h4>
                        {articles_html}
                    </div>
                </div>
                """
            reports_html += '</div>\n' # Close topic-section

        print("--- DEBUG: reports_html ---")
        print(reports_html)
        print("--- END DEBUG: reports_html ---")

        full_html = html_template.format(
            main_title=editorial.main_title,
            editorial_content=editorial.editorial_content,
            toc_items=toc_items,
            reports_html=reports_html
        )

        state.final_content = Newsletter(html_content=full_html)
        return state