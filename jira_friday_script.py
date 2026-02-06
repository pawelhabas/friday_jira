from jira import JIRA
from datetime import datetime
import pandas as pd
import os
from dataclasses import dataclass
from mailer import my_mail_sender


@dataclass
class JiraCreds:
    server: str
    user: str
    token: str


jira_creds = JiraCreds(
    server=os.getenv('SERVER', 'localhost'),
    user=os.getenv('USER', 'localhost'),
    token=os.getenv('TOKEN', 'localhost')
)

assert jira_creds.server != jira_creds.user != jira_creds.token, "Jira credentials missing"

try:
    jira = JIRA(server=jira_creds.server,
                basic_auth=(jira_creds.user, jira_creds.token))

    #   getting current issues
    my_issues = jira.search_issues('assignee = currentUser() AND Sprint in openSprints() ORDER BY priority DESC',
                                   maxResults=50)

    #   Upcoming week issues
    week_tasks = []
    for issue in my_issues:
        if issue.fields.priority.name in ['Highest', 'High'] and issue.fields.aggregatetimespent:
            week_tasks.append({
                'Key': issue.key,
                'Summary': issue.fields.summary[:80],
                'Priority': issue.fields.priority.name,
                'Estimate': f"{issue.fields.aggregatetimespent // 3600}h",
                'Link': issue.permalink()
            })

    #   Eksport to Markdown
    df = pd.DataFrame(week_tasks)
    md_content = f"# Plan na tydzień {datetime.now().strftime('%d.%m.%Y')}\n\n" + df.to_markdown(index=False)

    #   temporary file
    temp_file = f'zadania_tydz_{datetime.now().isocalendar()[1]}.md'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    #   Sending email
    my_mail_sender(
        text=f"📋 Oto Twój plan zadań na tydzień!\n\n{md_content}",
        attachments=[temp_file]
    )

    # remove temp file
    os.remove(temp_file)
    print("✅ Lista zadań wysłana mailem!")
except Exception as e:
    print(" >>> Something went wrong :( \n", type(e), e)
