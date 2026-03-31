# CIS 4394 Agentic AI Course Showcase

## Included files
- `index.html`: Student project showcase website with proposal links and dashboard summaries.
- `slides/CIS4394_Agentic_AI_Showcase.pptx`: Presentation deck (PowerPoint).
- `slides/index.html`: Legacy HTML deck (kept as backup).
- `demo/expense_agent.py`: Google ADK expense reimbursement demo with mock data.

## Open the showcase website
Double-click `index.html` in a browser. No build step or local server required.

## Open the presentation deck
Open `slides/CIS4394_Agentic_AI_Showcase.pptx` in PowerPoint/Keynote/Google Slides.

## Run the demo
1. Install dependency: `pip install google-adk`
2. Set API key: `export GOOGLE_API_KEY="your_key_here"`
3. Run: `python demo/expense_agent.py`

## Proposal links in project cards
Each student card now links directly to the student's submitted proposal file in the project folder.
If you later want to replace proposal links with deployed app links, edit the card-rendering logic in `index.html`.

## Update student metadata
If project names, domains, platforms, target customers, or descriptions change, edit the `students` array in `index.html`.
