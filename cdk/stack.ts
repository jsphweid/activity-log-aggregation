import * as cdk from "@aws-cdk/core";
import * as events from "@aws-cdk/aws-events";
import * as targets from "@aws-cdk/aws-events-targets";
import * as lambda from "@aws-cdk/aws-lambda";
import * as dynamodb from "@aws-cdk/aws-dynamodb";
import { PythonFunction } from "@aws-cdk/aws-lambda-python";

// import * as sqs from "@aws-cdk/aws-sqs";
// import * as lambdaEventSource from "@aws-cdk/aws-lambdas-event-sources";
// import * as s3 from "@aws-cdk/aws-s3";
// import * as iam from "@aws-cdk/aws-iam";
import * as apiGateway from "@aws-cdk/aws-apigateway";

import { Duration } from "@aws-cdk/core";
import { HostedZone } from "@aws-cdk/aws-route53";
// import { StreamViewType } from "@aws-cdk/aws-dynamodb";
// import { DynamoEventSource } from "@aws-cdk/aws-lambdas-event-sources";

export namespace ActivityLogAggregation {
  interface StackProps extends cdk.StackProps {
    env: {
      region: string;
      GITHUB_ACCESS_TOKEN: string;
      GITHUB_USER: string;
      NOTION_EMAIL: string;
      NOTION_TOKEN_V2: string;
      NOTION_SPACE_ID: string;
    };
  }

  export class Stack extends cdk.Stack {
    constructor(scope: cdk.Construct, id: string, props: StackProps) {
      super(scope, id, props);

      const table = new dynamodb.Table(this, "ActivityLogAggregationTable", {
        partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
        sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      });

      // Secondary sort effectively so we can quickly find the date
      // of the latest activity log per type. It can also be used to
      // filter out types in a regular search request
      table.addGlobalSecondaryIndex({
        projectionType: dynamodb.ProjectionType.ALL,
        partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
        sortKey: { name: "TypeSK", type: dynamodb.AttributeType.STRING },
        indexName: "GSI1",
      });

      const logAggregatorLambda = new PythonFunction(
        this as any,
        "LogAggregatorLambda",
        {
          entry: "../build",
          runtime: lambda.Runtime.PYTHON_3_8 as any,
          index: "aggregation_lambda.py",
          memorySize: 256,
          timeout: Duration.seconds(20) as any,
          environment: {
            DYNAMODB_TABLE_NAME: table.tableName,
            GITHUB_ACCESS_TOKEN: props.env.GITHUB_ACCESS_TOKEN,
            GITHUB_USER: props.env.GITHUB_USER,
            NOTION_EMAIL: props.env.NOTION_EMAIL,
            NOTION_TOKEN_V2: props.env.NOTION_TOKEN_V2,
            NOTION_SPACE_ID: props.env.NOTION_SPACE_ID,
          },
        }
      );

      const rule = new events.Rule(this, "Rule", {
        schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
      });

      rule.addTarget(new targets.LambdaFunction(logAggregatorLambda as any));
      table.grantReadWriteData(logAggregatorLambda as any);

      // Graphql Lambda that allows one to interact with the DB easier
      const fetchLambda = new PythonFunction(this as any, "FetchLambda", {
        entry: "../build",
        runtime: lambda.Runtime.PYTHON_3_8 as any,
        index: "fetch_lambda.py",
        memorySize: 128,
        timeout: Duration.seconds(10) as any,
        environment: {
          DYNAMODB_TABLE_NAME: table.tableName,
        },
      });

      table.grantReadData(fetchLambda as any);

      // NOTE: This is an explicit API (`proxy: false`) but all the other methods and possible
      // endpoints return 500s for now, which is not ideal, obviously it should return a
      // better http status code in the future
      const restApi = new apiGateway.LambdaRestApi(this, "fetchEndpoint", {
        handler: fetchLambda as any,
        proxy: false,
        deployOptions: {
          methodOptions: {
            "/*/*": { throttlingRateLimit: 3, throttlingBurstLimit: 5 },
          },
        },
      });

      const logs = restApi.root.addResource("logs");
      logs.addMethod("GET");
    }
  }
}
