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
import type { AttributeModel } from './AttributeModel';
import type { BeginEntryModel } from './BeginEntryModel';
import type { EndEntryModel } from './EndEntryModel';
import type { EndStreamModel } from './EndStreamModel';
import type { FirstItemStreamModel } from './FirstItemStreamModel';
import type { InitializeStreamModel } from './InitializeStreamModel';
import type { Span } from './Span';
/**
 * Log of  astep -- has a start and an end.
 */
export type Step = {
  step_start_log: BeginEntryModel;
  step_end_log: EndEntryModel | null;
  spans: Array<Span>;
  attributes: Array<AttributeModel>;
  streaming_events: Array<InitializeStreamModel | FirstItemStreamModel | EndStreamModel>;
};
