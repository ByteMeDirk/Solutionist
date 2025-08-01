import re

from transformers import pipeline

# Initialize the summarization pipeline with a lightweight model suitable for deployment
summarizer = pipeline(
    "summarization", model="facebook/bart-large-cnn", device=-1  # Use CPU
)


def clean_markdown(text):
    """Remove markdown syntax and code blocks for better summarization"""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    text = re.sub(r"`.*?`", "", text)
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def generate_summary(content, max_length=130, min_length=30):
    """
    Generate a summary of the solution content.
    Returns a concise summary string.
    """
    try:
        # Clean the content first
        cleaned_content = clean_markdown(content)

        # Skip if content is too short
        if len(cleaned_content.split()) < min_length:
            return cleaned_content[:250]

        # Generate summary
        summary = summarizer(
            cleaned_content,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,
        )[0]["summary_text"]

        return summary

    except Exception as e:
        # Fallback to a simple truncation if summarization fails
        return cleaned_content[:250] + "..."
