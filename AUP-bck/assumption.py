import os 
import json
import shutil

class Assumptions:

    def __init__(self, envFile_Path):
        self.envFile = envFile_Path
        self.logDirPath = './home/ubuntu/logs'
        self.loadEnvFile()

    def loadEnvFile(self):
        """ this function loeads env file """
        try:
            with open(self.envFile, 'r') as envFile:
                self.env = json.load(envFile)
            print(f">>> env file loaded: {self.envFile}")
            print(self.env["number_of_company"])
        except FileNotFoundError:
            print(f">>> env file not found: {self.envFile}")
            exit(1)

        # setting up paths 
        self.source_parent_dir = self.env["source_parent_dir"]
        self.target_parent_dir = self.env["target_parent_dir"]

    def makeDirs(self):
        """ this fucntion create all dirs and sub dirs too """
        os.makedirs(self.source_parent_dir, exist_ok=True)
        os.makedirs(self.target_parent_dir, exist_ok=True)
        os.makedirs(self.logDirPath, exist_ok=True)
        print(f">>> dir created.")

    def cleanUp(self):
        """ this function clean all stuffs which we created to full-fill assumption """
        
        if os.path.exists(self.source_parent_dir):
            shutil.rmtree(self.source_parent_dir)
        
        if os.path.exists(self.target_parent_dir):
            shutil.rmtree(self.target_parent_dir)
        
        print("CleanUp complete")

assume = Assumptions(
    envFile_Path = os.path.join(os.getcwd(), 'env/fwDevEnv.json')
)
# assume.makeDirs()
# assume.cleanUp()