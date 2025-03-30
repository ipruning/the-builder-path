from pocketflow import Flow

from nodes import AnswerNode, GetQuestionNode


def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()

    # Connect nodes in sequence
    get_question_node >> answer_node  # type: ignore

    # Create flow starting with input node
    return Flow(start=get_question_node)
