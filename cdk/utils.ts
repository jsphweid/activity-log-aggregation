import * as fs from "fs";
import * as rimraf from "rimraf";
import { ncp } from "ncp";

const copyDir = (
  source: string,
  dest: string,
  options: object = {}
): Promise<void> =>
  new Promise((resolve, reject) =>
    ncp(source, dest, options, (err) => (err ? reject(err) : resolve()))
  );

export const readEnvFile = (): any =>
  fs
    .readFileSync("../prod.env", "utf-8")
    .split("\n")
    .reduce(
      (prev, curr) => ({ ...prev, [curr.split("=")[0]]: curr.split("=")[1] }),
      {}
    );

// Hack to get python files in the right place for export
export const prepare = async () => {
  rimraf.sync("../build");
  fs.mkdirSync("../build");
  await copyDir(
    "../activity_log_aggregation/",
    "../build/activity_log_aggregation/"
  );
  await copyDir("../lambdas", "../build");
};
