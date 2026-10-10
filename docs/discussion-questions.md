# Discussion Questions (with expected answers)

Use 4–6 of these in Sections 7–8. Answers are short on purpose — let the room do the talking first.

1. **"If containers make apps portable, why do companies still have deployment problems?"**
   Containers solve packaging. Data access, security approvals, scaling, monitoring, cost control and ownership are still separate problems.

2. **"Our model works brilliantly in testing. What could still go wrong in production?"**
   Real inputs differ from test data (drift), traffic spikes, latency expectations, missing monitoring, nobody owns retraining, and silent quality decline while the service looks "up".

3. **"Should we call an LLM API or host our own model?"**
   API: fastest to start, pay per use, no GPU ops — but data leaves your boundary and you depend on a vendor. Self-host: control and data residency, potentially cheaper at very high volume — but needs GPUs, specialist skills and you pay even when idle. Most teams start with an API.

4. **"Why did the free app take a minute to respond at first?"**
   Free instances sleep when idle to save cost; the first request wakes a container (cold start). Paid always-on instances avoid this — a direct cost-vs-experience trade-off.

5. **"What happens if 10,000 people use this app at once?"**
   One 0.1-CPU container would be overwhelmed. Because the service is stateless and packaged as an image, you can run many identical containers behind a load balancer — this is what orchestration platforms and autoscaling are for.

6. **"Is a containerized application automatically secure?"**
   No. You still need patched base images, non-root users, secret management, input validation, network rules, access control and vulnerability scanning.

7. **"Where should an API key for an LLM provider live?"**
   In the platform's secret/environment-variable store — never in code, the Dockerfile, the image or Git history. Rotate it if it ever leaks.

8. **"How would you know if the model starts giving worse answers?"**
   Monitor model-level metrics, not just uptime: sample predictions for human review, track confidence distributions and user feedback, compare against a labelled evaluation set periodically.

9. **"What's the difference between containerization and deployment?"**
   Containerization = packaging the app and its environment into an image. Deployment = running that image somewhere reachable, health-checked, monitored and updatable.

10. **"What would you need to change to turn this demo into a production service?"**
    A better model and evaluation data, authentication/rate limiting, paid always-on compute with more than one instance, monitoring and alerting, logging to persistent storage, a CI pipeline running tests before deploy, and a clear owner.
