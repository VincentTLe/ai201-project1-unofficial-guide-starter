"""Step 6: a small Gradio web UI for The Unofficial Knox Guide.

Type a question, get a grounded answer plus the documents it was drawn from.

Run it (then open http://localhost:7860):
    python src/app.py
"""

import gradio as gr

from generate import ask


def handle_query(question):
    if not question.strip():
        return "", ""
    result = ask(question)
    # turn the source filename list into a little bullet list for display
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources — not enough info)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Knox Guide") as demo:
    gr.Markdown(
        "# The Unofficial Knox Guide\n"
        "Ask about Knox College student life — professors, dining, housing, campus life. "
        "Answers come only from real student reviews and The Knox Student, with sources."
    )
    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. Is the housing lottery actually random?",
    )
    ask_btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    # clicking the button OR pressing Enter in the textbox both run the query
    ask_btn.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
