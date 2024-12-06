from phi.model.ollama import Ollama
from phi.tools.calculator import Calculator
from phi.tools.exa import ExaTools
from phi.tools.file import FileTools
from phi.tools.googlesearch import GoogleSearch
from phi.tools.pandas import PandasTools
from phi.tools.shell import ShellTools
from phi.tools.wikipedia import WikipediaTools
from phi.tools.sleep import Sleep
from dotenv import load_dotenv
from cdp import *
import os
import json
from phi.agent import Agent
from phi.model.ollama import Ollama
from cdp.errors import UnsupportedAssetError
from Creator import ChatbotAnalyzer

load_dotenv()

API_KEY_NAME = os.environ.get("CDP_API_KEY_NAME")
PRIVATE_KEY = os.environ.get("CDP_PRIVATE_KEY", "").replace('\\n', '\n')
Cdp.configure(API_KEY_NAME, PRIVATE_KEY)

class OnChainAgents:
    def __init__(self, Wallet_Id=None):
        """
        Initializes the OnChainAgents class.

        The constructor checks if a Wallet_Id is provided. If not, it creates a new wallet.
        If a Wallet_Id is given, it attempts to fetch the wallet data associated with that ID.
        
        Parameters:
        Wallet_Id (str): Optional; If provided, attempts to load an existing wallet. 
                         If None, creates a new wallet.
        """
        self.WalletStorage = "wallet_storage"

        if not os.path.exists(self.WalletStorage):
            os.makedirs(self.WalletStorage)
            print(f"Directory '{self.WalletStorage}' created successfully.")

        if Wallet_Id is None:
            self.wallet = Wallet.create()
        else:
            fetched_data = self.fetch(Wallet_Id)
            if fetched_data:
                data = WalletData(wallet_id=fetched_data['wallet_id'], seed=fetched_data['seed'])
                self.wallet = Wallet.import_data(data)
            else:
                raise ValueError(f"Wallet with ID {Wallet_Id} could not be found.")

    def fetch(self, wallet_id):
        """
        Fetches the wallet data from a JSON file.

        This method constructs the file path for the specified wallet ID and attempts to read
        the corresponding JSON file. If the file exists, it loads the data and returns it as a dictionary.

        Parameters:
        wallet_id (str): The ID of the wallet to fetch.

        Returns:
        dict or None: The wallet data dictionary if found, else None.
        """
        file_path = os.path.join(self.WalletStorage, f"{wallet_id}.json")

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data_dict = json.load(file)
            print(f"Wallet data for {wallet_id} successfully fetched.")
            return data_dict
        else:
            print(f"No wallet data found for ID: {wallet_id}.")
            return None
        
    def store(self, data_dict):
        """
        Stores the wallet data securely in a JSON file.

        This method takes a dictionary containing wallet data and writes it to a JSON file
        named after the wallet ID. It ensures that the data is saved in a structured format.

        Parameters:
        data_dict (dict): Dictionary containing wallet data.
        """
        wallet_id = data_dict.get("wallet_id")
        file_path = os.path.join(self.WalletStorage, f"{wallet_id}.json")

        with open(file_path, 'w') as file:
            json.dump(data_dict, file)
        print(f"Wallet data for {wallet_id} successfully stored.")

    def save_wallet(self):
        """
        Exports and saves the current wallet's data and seed to files.

        This method exports the current state of the wallet and stores it in JSON format.
        It also saves the seed securely in an encrypted format and logs the wallet ID
        in a separate text file if it does not already exist.

        The process includes checking for existing IDs to prevent duplicates.
        """
        data = self.wallet.export_data()
        self.store(data.to_dict())
        
        seed_file_path = "my_seed.json"
        self.wallet.save_seed(seed_file_path, encrypt=True)

        wallet_id = data.wallet_id
        id_file_path = "wallet_ids.txt"

        if not self.wallet_id_exists(wallet_id, id_file_path):
            with open(id_file_path, "a") as id_file:
                id_file.write(f"{wallet_id}\n")
                print(f"Wallet ID {wallet_id} saved to wallet_ids.txt.")
        else:
            print(f"Wallet ID {wallet_id} already exists in wallet_ids.txt.")

    def wallet_id_exists(self, wallet_id, file_path):
        """
        Checks if a given wallet ID exists in the specified text file.

        This method reads through a text file containing existing wallet IDs to determine
        whether the specified ID is present.

        Parameters:
        wallet_id (str): The ID of the wallet to check.
        
        Returns:
        bool: True if the ID exists, False otherwise.
        """
        if os.path.exists(file_path):
            with open(file_path, 'r') as id_file:
                existing_ids = id_file.read().splitlines()
                return wallet_id in existing_ids
        return False
    
def main():
    """
    Main function to run the OnChainAgents interface.
    Provides an interactive loop for loading models and asking questions.
    """
    while True:

        Tools = {
            "Calculator": Calculator(add=True, subtract=True, multiply=True, divide=True, exponentiate=True, factorial=True, is_prime=True, square_root=True),
            "Exa": ExaTools(api_key=os.getenv("EXA_API_KEY")),
            "File": FileTools(),
            "GoogleSearch": GoogleSearch(),
            "Pandas": PandasTools(),
            "Shell": ShellTools(),
            "Wikipedia": WikipediaTools(),
            "Sleep": Sleep()
        }
        def get_balance(asset_id) -> str:
            """
            Get the balance of a specific asset in the agent's wallet.
            
            Parameters:
            asset_id (str): Asset identifier ("eth", "usdc") or contract address of an ERC-20 token
            
            Returns:
            str: A message showing the current balance of the specified asset.
            """
            balance = agent.wallet.balance(asset_id)
            return f"Current balance of {asset_id}: {balance}"

        def create_token(name, symbol, initial_supply):
            """
            Create a new ERC-20 token.
            
            Parameters:
            name (str): The name of the token.
            symbol (str): The symbol of the token.
            initial_supply (int): The initial supply of tokens.
            
            Returns:
            str: A message confirming the token creation with details.
            """
            deployed_contract = agent.wallet.deploy_token(name, symbol, initial_supply)
            deployed_contract.wait()
            return f"Token {name} ({symbol}) created with initial supply of {initial_supply} and contract address {deployed_contract.contract_address}"

        def transfer_asset(amount, asset_id, destination_address):
            """
            Transfer an asset to a specific address.
            
            Parameters:
            amount (Union[int, float, Decimal]): Amount to transfer.
            asset_id (str): Asset identifier ("eth", "usdc") or contract address of an ERC-20 token.
            destination_address (str): Recipient's address.
            
            Returns:
            str: A message confirming the transfer or describing an error.
            """
            try:
                is_mainnet = agent.wallet.network_id == "base-mainnet"
                is_usdc = asset_id.lower() == "usdc"
                gasless = is_mainnet and is_usdc
                if asset_id.lower() in ["eth", "usdc"]:
                    transfer = agent.wallet.transfer(amount,
                                                    asset_id,
                                                    destination_address,
                                                    gasless=gasless)
                    transfer.wait()
                    gasless_msg = " (gasless)" if gasless else ""
                    return f"Transferred {amount} {asset_id}{gasless_msg} to {destination_address}"
                
                try:
                    balance = agent.wallet.balance(asset_id)
                except UnsupportedAssetError:
                    return f"Error: The asset {asset_id} is not supported on this network. It may have been recently deployed. Please try again in about 30 minutes."

                if balance < amount:
                    return f"Insufficient balance. You have {balance} {asset_id}, but tried to transfer {amount}."

                transfer = agent.wallet.transfer(amount, asset_id, destination_address)
                transfer.wait()
                return f"Transferred {amount} {asset_id} to {destination_address}"
                    
            except Exception as e:
                return f"Error transferring asset: {str(e)}. If this is a custom token, it may have been recently deployed. Please try again in about 30 minutes, as it needs to be indexed by CDP first."

        def mint_nft(contract_address, mint_to):
            """
            Mint an NFT to a specified address.
                
            Parameters:
            contract_address (str): Address of the NFT contract.
            mint_to (str): Address to mint NFT to.
                
            Returns:
            str: Status message about the NFT minting.
            """
            try:
                mint_args = {"to": mint_to, "quantity": "1"}

                mint_invocation = agent.wallet.invoke_contract(
                    contract_address=contract_address, method="mint", args=mint_args)
                mint_invocation.wait()

                return f"Successfully minted NFT to {mint_to}"

            except Exception as e:
                return f"Error minting NFT: {str(e)}"
            
        def read_json_data(file_path: str) -> dict:
            """
            Reads data from a JSON file and returns it as a dictionary.

            Args:
                file_path (str): The path to the JSON file.

            Returns:
                dict: The data read from the JSON file, or None if an error occurred.
            """
            try:
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    return data
            except FileNotFoundError:
                print(f"Error: The file {file_path} does not exist.")
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON from the file.")
            except Exception as e:
                print(f"An error occurred: {e}")
            return None
        
        load_model = input("Do you want to load an existing model? (yes/no): ").strip().lower()
        
        if load_model == 'yes':
            wallet_id = input("Enter your Wallet ID: ")
            agent = OnChainAgents(Wallet_Id=wallet_id)
            print(f"Loaded model for Wallet ID: {wallet_id} and public address {agent.wallet.default_address.address_id}.")
            file_path = f"DB/{agent.wallet.default_address.address_id}.json"
            data = read_json_data(file_path)
            ToolKit = []
            if data:
                for key in data["Tools"]:
                    if key in Tools.keys():
                        ToolKit.append(Tools[key])
            based_agent = Agent(
                model=Ollama(id="llama3.2"),
                tools=[get_balance, create_token, transfer_asset, mint_nft,ExaTools(api_key=os.getenv("EXA_API_KEY"))]+ToolKit,
                description=data["Personality"],
                instructions=[
                    "Always display the balance when asked.",
                    "Everything you do is not a simulation but instead real-life actions."
                ] + [data["Instructions"]],
            )
            while True:
                prompt = input("Ask:")
                if prompt.lower() == 'exit':
                    agent.save_wallet()
                    print("Wallet saved. Exiting...")
                    break
                based_agent.print_response(prompt)
            break
        
        elif load_model == 'no':
            agent = OnChainAgents()
            prompt1 = input("How do you want your chatbot to be:")
            print(f"Created a new model with public address {agent.wallet.default_address.address_id}.")
            creater = ChatbotAnalyzer()
            tools, concepts = creater.find_tools_and_concepts(prompt1)
            personality = creater.GeneratePersonality(prompt1)
            instructions = creater.GenerateInstructions(prompt1)
            creater.save_to_json(tools, personality, instructions, concepts,agent.wallet.default_address.address_id)
            file_path = f"DB/{agent.wallet.default_address.address_id}.json"
            data = read_json_data(file_path)
            ToolKit = []
            if data:
                for key in data["Tools"]:
                    if key in Tools.keys():
                        ToolKit.append(Tools[key])
            based_agent = Agent(
                model=Ollama(id="llama3.2"),
                tools=[get_balance, create_token, transfer_asset, mint_nft,ExaTools(api_key=os.getenv("EXA_API_KEY"))]+ToolKit,
                description=data["Personality"],
                instructions=[
                    "Always display the balance when asked.",
                    "Everything you do is not a simulation but instead real-life actions."
                ] + [data["Instructions"]],
            )
            while True:
                prompt = input("Ask:")
                if prompt.lower() == 'exit':
                    agent.save_wallet()
                    print("Wallet saved. Exiting...")
                    break
                based_agent.print_response(prompt)
            break

        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            continue

main()