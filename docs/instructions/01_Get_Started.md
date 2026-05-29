# Part 1 - Get started

## Sign in to Windows

**Step 1:** As a first step, login into the lab Virtual Machine using the credentials below:

**Password:** +@lab.VirtualMachine(VirtualMachineName).Password+

> [!TIP]
>  First time using **Skillable?** The green "T" (e.g., +++Admin+++) indicates values that are automatically input for you at the current cursor location in VM, with one click. This reduces your effort and minimizes input errors.
> Also, you can always click on the images to enlarge them, if needed.

## Open workshop in Visual Studio Code

In this workshop, we will be using **Visual Studio Code** as our development environment. It is equipped with all the necessary tools and dependencies pre-installed. This will allow you to focus on learning and prototyping without worrying about local setup.

1. To launch Visual Studio code, you can either click on the icon in the home page, or search for Visual Studio Code in the start up menu, or Click on the Visual Studio icon that is pinned to the task bar. 

2. In the Visual Studio Code, open a new terminal (**Terminal → New Terminal**) and run the setup script to populate your `.env` file with your Microsoft Foundry credentials:

> [!TIP]
>  Ensure the default terminal launched is bash. If not, switch the terminal by clicking the **down arrow,** next to the add icon and select **bash** to ensure the default terminal is bash.

```bash
/src/scripts/get-env
```

This will create a `.env` file in the repo root with values for:

```
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
API_KEY=<your-key>
```

## Login in to Azure 

1. Next, open the edge browser and navigate to <[https://ai.azure.com/nextgen](https://ai.azure.com/nextgen)

2. Sign-in with the following credentials:
   -  Username: +++@lab.CloudPortalCredential(User1).Username+++
   -  TAP: +++@lab.CloudPortalCredential(User1).TAP+++

3. Once you are signed in, head back to **Visual Studio Code** to continue with the lab.

## Validate setup using Notebook 01

1. Head back to Visual Studio Code and confirm a `.env` file has been created successfully.

1. In the VS Code Explorer panel (left sidebar), expand the **`src/`** folder.
2. Click on **`01-introduction-setup.ipynb`** to open it.
3. At the top of the notebook click the **Run All** command to execute the notebook. A pop up will be created, select: **Python Environments... > Python 3.13....**, you will have successfully executed the notebook.

## What have you achieved?

As you work through the cells in `01-introduction-setup.ipynb` in order, you will see:

1. **Install dependencies** — Installs required Python packages (`openai`, `python-dotenv`, `requests`, `matplotlib`, `tabulate`, `azure-ai-projects`, `aiohttp`). This may take 1–2 minutes.
2. **Import libraries and connect to Microsoft Foundry** — Loads your `.env` file and creates an AIProjectClient pointed at your Microsoft Foundry endpoint.
3. **Verify your environment** — Confirms all required environment variables are set and that the data files exist.

> [!NOTE]
> If the verification cell reports missing environment variables, double-check your `.env` file at the repo root. If it's missing, re-run `/src/scripts/get-env` in the terminal.

### ✅ Setup Complete

Once all three setup cells pass with no errors, your environment is ready. You should see a confirmation message in the last cell output.

Click **Next** to meet the Zava agent and see it in action.
