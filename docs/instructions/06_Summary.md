# Summary

Congratulations on completing **LAB 521: Improving Agent Behavior Using Reinforcement Learning from Traces**!

## What You Learned

In this lab, you worked through the full RFT workflow on a real agentic task:

- **Ran a live agent** — ran Zava's return-resolution agent on real customer scenarios, observing tool calling and policy application in action
- **Defined "good behavior"** — built a grader function with partial credit scoring that evaluates action accuracy, dollar amounts, policy reasoning, and tool usage
- **Established a baseline** — measured base `o4-mini` at ~73% on validation scenarios and calibrated the pass threshold for optimal RL signal
- **Built training data** — explored the RFT data format, constructed a custom example, and understood why prompt diversity matters more than volume
- **Submitted a real RFT job** — uploaded data, embedded the grader, and launched a fine-tuning job on Microsoft Foundry
- **Evaluated results** — analyzed the reward curve, compared checkpoints, and confirmed a ~73% → ~96% improvement in policy-following accuracy

## Lab Recap

| Notebook | What You Did |
|----------|-------------|
| **01 – Introduction & Setup** | Connected to Microsoft Foundry, verified environment |
| **02 – Meet the Agent** | Ran the Zava agent live on 3 scenarios, saw tool calling in action |
| **03 – Baseline & Grader** | Evaluated base o4-mini (~73%), understood the grader and threshold calibration |
| **04 – Build Data & Submit** | Explored training data format, built a custom example, submitted an RFT job |
| **05 – Training Results & Evaluate** | Analyzed reward curves, compared checkpoints, confirmed ~96% fine-tuned accuracy |

## Check Your Submitted Job

Your RFT job from notebook 04 will finish in about **10 hours**. Open `src/06-wrap-up.ipynb` and run the job status cell to check on it. Once it completes, you can deploy the best checkpoint and run the head-to-head evaluation with your own fine-tuned model.

## Next Steps & Experiments

Once your job completes, try these variations to deepen your understanding:

| Experiment | What to Change | Expected Effect |
|-----------|---------------|----------------|
| **Tighter threshold** | `pass_threshold=0.90` | Stricter compliance, slower convergence |
| **More training data** | Add more scenario variations | Better generalization to unseen cases |
| **Grader weights** | Increase action weight to 60% | Model prioritizes correct action over amounts |
| **Longer training** | `n_epochs=5` | May improve accuracy but risks overfitting—watch the reward curve |

## Applying RFT to Your Own Agent

The workflow you followed in this lab applies to any agentic task where:
- The agent uses tools to fetch data
- "Correctness" can be defined by a scoring function (even approximately)
- The model shows inconsistent behavior with prompting alone

Key things needed to apply RFT to your own scenario:
1. **A diverse set of prompts** — 50–400 examples covering your edge cases
2. **A grader function** — Python code that scores model outputs on 0.0–1.0
3. **A calibrated pass threshold** — target 30–50% failure rate on your baseline model

## Resources

| Resource | Description |
|----------|-------------|
| [Azure AI Fine-Tuning docs](https://learn.microsoft.com/azure/ai-services/openai/how-to/fine-tuning) | Official documentation for fine-tuning on Azure AI |
| [RFT with graders guide (OpenAI)](https://platform.openai.com/docs/guides/reinforcement-fine-tuning) | Detailed guide on RFT grader design and data format |
| [RFT Lessons Learned](../rft-lessons-learned.md) | Hard-won lessons from building this lab — grader selection, partial credit, checkpoint evaluation |
| [Facilitator Setup Guide](../facilitator-setup.md) | How to deploy the infrastructure for this lab in your own environment |
| [Build 2026 Next Steps](https://aka.ms/build26-next-steps) | Continue your learning journey after Build 2026 |

## Try This at Home

This lab is available for you to revisit at your own pace. You can find the complete code, data, and instructions in the official GitHub repository:

**[https://github.com/microsoft/Build26-LAB521](https://github.com/microsoft/Build26-LAB521)**

---

### 🎉 Thank you for completing LAB 521!
