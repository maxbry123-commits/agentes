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
import type { PointerModel } from './PointerModel';
/**
 * Stores data about a child application (either a fork or a spawned application).
 * This allows us to link from parent -> child in the UI.
 */
export type ChildApplicationModel = {
  type?: string;
  child: PointerModel;
  event_time: string;
  event_type: ChildApplicationModel.event_type;
  sequence_id: number | null;
};
export namespace ChildApplicationModel {
  export enum event_type {
    FORK = 'fork',
    SPAWN_START = 'spawn_start'
  }
}
