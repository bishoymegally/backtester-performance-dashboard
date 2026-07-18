import json
import os
def save_metrics(metrics, experiment_name):
    os.makedirs("experiments", exist_ok=True)
    current_exp = os.path.join("experiments", experiment_name)
    os.makedirs(current_exp, exist_ok=True)
    if len(os.listdir(current_exp)) == 0:
        num = 1
    else:
        num = int(sorted(os.listdir(current_exp))[-1][-8:-5]) + 1
    current_file = os.path.join(current_exp, f"metrics{num:03d}.json")

    with open(current_file, "w") as file:
        json.dump(metrics, file)



def load_metrics():
    folder_name = "experiments"
    list_of_exp = []   
    if os.path.exists(folder_name):
        if len(os.listdir(folder_name)) == 0:
            print("There are no experiments")
            return 
        for experiment_name in os.listdir(folder_name):
            
            experiment_path = os.path.join(folder_name, experiment_name)
            
            if not os.path.isdir(experiment_path):
                continue
            
            list_runs = []

            for run in os.listdir(experiment_path):

                run_path = os.path.join(experiment_path, run)

                with open(run_path, "r") as file:
                    output = json.load(file)
                list_runs.append(output)
            list_of_exp.append([experiment_name, list_runs])
    else:
         print("Folder with such name doesn't exist")
         return
    return list_of_exp


