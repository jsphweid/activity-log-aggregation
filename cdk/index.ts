// NOTE: this file is just a reference implementation

import { App } from "@aws-cdk/core";

import { ActivityLogAggregation } from "./stack";
import { prepare, readEnvFile } from "./utils";

const REGION = process.env.REGION;

const app = new App();

prepare().then(() => {
  new ActivityLogAggregation.Stack(app, "ActivityLogAggregation", {
    env: { region: REGION || "us-west-2", ...readEnvFile() },
    hostedZoneName: "josephweidinger.com",
  });

  app.synth();
});
