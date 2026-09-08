/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationModel } from './ApplicationModel';
import type { ChildApplicationModel } from './ChildApplicationModel';
import type { PointerModel } from './PointerModel';
import type { Step } from './Step';
/**
 * Application logs are purely flat --
 * we will likely be rethinking this but for now this provides for easy parsing.
 */
export type ApplicationLogs = {
  application: ApplicationModel;
  children: Array<ChildApplicationModel>;
  steps: Array<Step>;
  parent_pointer?: PointerModel | null;
  spawning_parent_pointer?: PointerModel | null;
};
