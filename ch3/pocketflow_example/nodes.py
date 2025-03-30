from pocketflow import Node

from utils.call_llm import call_llm


class GetQuestionNode(Node):
    def exec(self, _):
        user_question = input("Enter your question: ")
        return user_question

    def post(self, shared, prep_res, exec_res):
        shared["question"] = exec_res
        return "default"


class AnswerNode(Node):
    def prep(self, shared):
        return shared["question"]

    def exec(self, question):
        return call_llm(question)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
