import json
import os
from phi.agent import Agent, RunResponse
from phi.model.ollama import Ollama

class ChatbotAnalyzer:
    """
    ChatbotAnalyzer is a class that facilitates the creation of chatbots by analyzing user prompts,
    generating personalities, and defining instructions for the chatbot's functionalities.
    """

    def __init__(self):
        """
        Initializes the ChatbotAnalyzer with a toolkit of available tools and sets up agents for analysis,
        personality generation, and instruction generation using the Ollama model.
        """
        self.tool_kit = {
            "Calculator": "Calculator enables an Agent to perform mathematical calculations.",
            "Exa": "ExaTools enable an Agent to search the web using Exa.",
            "File": "FileTools enable an Agent to read and write files on the local file system.",
            "GoogleSearch": "GoogleSearch enables an Agent to perform web crawling and scraping tasks.",
            "Pandas": "PandasTools enable an Agent to perform data manipulation tasks using the Pandas library.",
            "Shell": "ShellTools enable an Agent to interact with the shell to run commands.",
            "Wikipedia": "WikipediaTools enable an Agent to search Wikipedia and add its contents to the knowledge base.",
            "Sleep": "Tool to pause execution for a given number of seconds."
        }
        
        self.Analayser = Agent(
            model=Ollama(id="llama3.2"),
            instructions=[
                f"Based on the prompt provided give an analysis of what all tools from {self.tool_kit} should the chatbot be equipped with and what concepts should it know.",
                "The output should be of form [Tools = [the tools required], Concepts = [the concepts required]].",
                "Make sure only the structured output is given as output. No extra context or words should be included."
            ]
        )
        
        self.PersonalityGenerator = Agent(
            model=Ollama(id="llama3.2"),
            instructions=[
                "Based on the type of chatbot the user wants to make, generate a background and personality for the Chatbot to be created.",
                "Keep the whole background and personality concise and in a single paragraph.",
                "Output only the paragraph and let the para be like introducing the person. It should start with something like 'You are ...'"
            ]
        )

        self.InstructionGenerator = Agent(
            model=Ollama(id="llama3.2"),
            instructions=[
                "Based on the type of chatbot the user wants to create, generate a concise set of instructions outlining the tasks and functionalities that the chatbot should perform.",
                "The output should be structured as a para of actionable items, each describing a specific capability or task the chatbot is expected to handle.",
                "Output only the para without any additional context or words.",
                "The text should be as if it is instructing someone.",
                "For example if the user wants a math teacher u should specify what all the chatbot should do to fulfill the duties of a math teacher.",
                "Start with 'Instructions are ...'"
            ]
        )

    def find_tools_and_concepts(self, prompt):
        """
        Analyzes a given prompt to determine which tools from the toolkit are needed 
        and what concepts are relevant for creating a chatbot.

        Parameters:
        prompt (str): The user-defined prompt describing desired chatbot functionalities.

        Returns:
        tuple: A tuple containing:
               - List of tools identified as necessary for the chatbot.
               - List of concepts extracted from the analysis.
        """
        run: RunResponse = self.Analayser.run(prompt)
        response = run.content
        original_string = response
        
        keywords = []
        
        for key in self.tool_kit.keys():
            if key in response:
                keywords.append(key)

        start_index = original_string.find("Concepts = [") + len("Concepts = [")
        end_index = original_string.find("]", start_index)
        
        concepts_string = original_string[start_index:end_index].strip()
        concepts_string = concepts_string.replace("'", "").strip()

        return keywords, concepts_string.split(", ")
    
    def GeneratePersonality(self, prompt):
        """
        Generates a personality description for the chatbot based on user input.

        Parameters:
        prompt (str): The user-defined prompt indicating desired characteristics of the chatbot.

        Returns:
        str: A concise paragraph describing the personality of the chatbot.
        """
        run: RunResponse = self.PersonalityGenerator.run(prompt)
        return run.content
    
    def GenerateInstructions(self, prompt):
        """
        Generates actionable instructions outlining what tasks and functionalities 
        the chatbot should perform based on user input.

        Parameters:
        prompt (str): The user-defined prompt indicating desired functionalities of the chatbot.

        Returns:
        str: A paragraph detailing specific capabilities or tasks for the chatbot.
        """
        run: RunResponse = self.InstructionGenerator.run(prompt)
        return run.content

    def save_to_json(self, tools, personality, instructions, concepts,ID):
        """
        Saves collected data about tools, personality, instructions, 
        and concepts into a JSON file for future reference.

        Parameters:
        tools (list): List of tools required by the chatbot.
        personality (str): Personality description of the chatbot.
        instructions (str): Instructions detailing tasks for the chatbot.
        concepts (list): List of relevant concepts for understanding.
        
        Returns:
        None
        This function creates a directory if it doesn't exist 
        and writes data into 'chatbot_data.json'.
        """
         
        os.makedirs('DB', exist_ok=True)

        data = {
            'Tools': tools,
            'Personality': personality,
            'Instructions': instructions,
            'Concepts': concepts
        }

        file_path = os.path.join('DB', f'{ID}.json')
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)