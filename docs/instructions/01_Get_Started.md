# Get started
<!-- TODO: add screenshots -->
## Sign in to Windows

As a first step, login into the lab Virtual Machine using the credentials you can find in the **Resources tab** under the Skillable VM name.

<!-- ![VM login credentials](../../img/vm_login_credentials.png) -->

> [!TIP]
>  First time using **Skillable?** The green "T" (e.g., +++Admin+++) indicates values that are automatically input for you at the current cursor location in VM, with one click. This reduces your effort and minimizes input errors.
> Also, you can always click on the images to enlarge them, if needed.

## Open workshop in a GitHub Codespace

In this workshop, we will be using **GitHub Codespaces** to launch a cloud-hosted development environment with all the necessary tools and dependencies pre-installed. This will allow you to focus on learning and prototyping without worrying about local setup.

To launch a codespace you need a **GitHub account**. Follow the instructions below to sign-in with a given GitHub Enterprise (GHE) account and create a GitHub Codespace for this lab.

1. Open the edge browser from the taskbar. You'll get a browser tab with the GHE sign-in page already opened for you.

2. Sign-in with the following credentials:
   -  Username: +++@lab.CloudPortalCredential(User1).Username+++
   -  TAP: +++@lab.CloudPortalCredential(User1).TAP+++

3. Once you are signed in, you'll be redirected to the [GitHub repo](https://github.com/microsoft/Build26-LAB521) hosting the lab code and resources.

4. Next, click on the green **Code** button and select **Create codespace on main** from the **Codespaces** tab.

    <!-- ![Create Codespace](../../img/create_codespace.png) -->

> [!WARNING]
> The codespace creation process might take a few minutes, as all the necessary dependencies and tools are being set up in the cloud environment.

5. Once the codespace is created, you'll see a Visual Studio Code environment loaded in your browser.
<!-- ![Codespace layout](../../img/codespace_layout.png) -->

6. You might choose to continue working in the browser or click on the **Open in VS Code** button to open it in the desktop application (recommended option).

    <!-- ![Open in VS Code](../../img/open_in_vscode.png) -->

7. If you choose to open it in the desktop application, you'll be prompted to confirm opening the VS Code Desktop app. Click **Open** to proceed.

> [!NOTE]
> You'll also get a popup *"All done. You can close this tab now."* in the browser, that you can just ignore.

<!-- ![Confirm opening VS Code App](../../img/confirm_opening_vscode.png) -->

8. Once VS Code Desktop is opened, you'll be asked to allow access to the codespace. Click **Open** to proceed.

<!-- ![Open Codespaces in VS Code Desktop](../../img/open_codespaces_vscode.png) -->

9. Next, you'll be asked to sign in to GitHub from VS Code. By clicking **Allow**, a browser window will open to complete the sign-in process. Click **Continue** to proceed with the GitHub Enterprise account you used to create the Codespace. And then click on **Authorize Visual Studio Code** to complete the sign-in process. Also, when asked to allow VS Code access to public and private networks, click **Allow**.

10. Once the sign-in process is completed, the site will try to redirect you back to VS Code. Click on the **Open** button to proceed.
<!-- ![Redirect back to VS Code](../../img/redirect_back_to_vscode.png) -->

11. Back in VS Code, you are now set to start working in the codespace environment. You should see a layout pretty similar to what you had in the browser.

## Login to Azure

In the GitHub Codespace, open a new terminal (**Terminal → New Terminal**) and run the setup script to populate your `.env` file with your Azure AI Foundry credentials:

```bash
/get.env
```

When prompted, enter the following credentials:
-  Email: +++@lab.CloudPortalCredential(User1).Username+++
-  TAP: +++@lab.CloudPortalCredential(User1).TAP+++

This will create a `.env` file in the repo root with values for:

```
AZURE_OPENAI_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>/openai/v1/
AZURE_OPENAI_API_KEY=<your-key>
```

> [!TIP]
> You can find your Azure AI Foundry endpoint and API key in the **Resources tab** of your Skillable environment.

> [!WARNING]
> Never commit your `.env` file to version control. It is already listed in `.gitignore` for this repo.

## Got issues when logging in with GitHub?

> [!NOTE]
> If you are properly logged in with the GHE account as per previous step, please ignore this section and move to the next one.

If you encounter issues when logging in with the given GHE account, you can always use your own, by following the steps below:

1. Navigate to the [GitHub repo](https://github.com/microsoft/Build26-LAB521) hosting the lab code and resources.

    > [!TIP]
    > Click the Star button in the top right corner, this will help you easily find it later.

2. To launch a codespace, you need a **GitHub account**.

    > [!NOTE]
    > If you already have a GitHub account, you can move to step 3 directly.

    To create one, click on the **Sign up** button and follow the instructions below:
    - In the new window, enter a personal email address, create a password, and choose a username.
    - Select your Country/Region and agree to the terms of service.
    - Click on the **Create account** button and wait for the verification email to arrive in your inbox.

    <!-- ![GitHub Account Sign Up](../../img/github_signup.png) -->

    - Copy the verification code from the email and paste it into the verification field on the GitHub website. Then click on **Continue**.
    - Once the account is created, you'll be redirected back to the GitHub repo page and you'll see a green banner at the top, like the one in the screenshot below.

    <!-- ![GitHub Repo Banner](../../img/github_repo_banner.png) -->

3. Click on **Sign in** and enter your GitHub credentials to log in. If you just created your account, use the username and password you set during the sign-up process.

## Open Notebook 01

Once your Codespace is open and your `.env` file is configured:

1. In the VS Code Explorer panel (left sidebar), expand the **`src/`** folder.
2. Click on **`01-introduction-setup.ipynb`** to open it.
3. When prompted to select a kernel, choose **Python 3** (or the environment that has the lab dependencies installed).

## Run the Setup Cells

Work through the cells in `01-introduction-setup.ipynb` in order:

1. **Install dependencies** — Installs required Python packages (`openai`, `python-dotenv`, `requests`, `matplotlib`, `tabulate`). This may take 1–2 minutes.
2. **Import libraries and connect to Azure AI Foundry** — Loads your `.env` file and creates an OpenAI client pointed at your Azure AI Foundry endpoint.
3. **Verify your environment** — Confirms all required environment variables are set and that the data files exist.

> [!NOTE]
> If the verification cell reports missing environment variables, double-check your `.env` file at the repo root. If it's missing, re-run `/get.env` in the terminal.

### ✅ Setup Complete

Once all three setup cells pass with no errors, your environment is ready. You should see a confirmation message in the last cell output.

Click **Next** to meet the Zava agent and see it in action.
