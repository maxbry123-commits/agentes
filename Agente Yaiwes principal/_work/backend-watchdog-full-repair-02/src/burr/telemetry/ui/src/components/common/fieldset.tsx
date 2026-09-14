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

/**
 * Tailwind catalyst component
 */

import {
  Description as HeadlessDescription,
  Field as HeadlessField,
  Fieldset as HeadlessFieldset,
  Label as HeadlessLabel,
  Legend as HeadlessLegend,
  type DescriptionProps as HeadlessDescriptionProps,
  type FieldProps as HeadlessFieldProps,
  type FieldsetProps as HeadlessFieldsetProps,
  type LabelProps as HeadlessLabelProps,
  type LegendProps as HeadlessLegendProps
} from '@headlessui/react';
import clsx from 'clsx';
import type React from 'react';

export function Fieldset({ className, ...props }: { disabled?: boolean } & HeadlessFieldsetProps) {
  return (
    <HeadlessFieldset
      {...props}
      className={clsx(className, '[&>*+[data-slot=control]]:mt-6 [&>[data-slot=text]]:mt-1')}
    />
  );
}

export function Legend({ ...props }: HeadlessLegendProps) {
  return (
    <HeadlessLegend
      {...props}
      data-slot="legend"
      className={clsx(
        props.className,
        'text-base/6 font-semibold text-zinc-950 data-[disabled]:opacity-50 sm:text-sm/6 dark:text-white'
      )}
    />
  );
}

export function FieldGroup({ className, ...props }: React.ComponentPropsWithoutRef<'div'>) {
  return <div {...props} data-slot="control" className={clsx(className, 'space-y-8')} />;
}

export function Field({ className, ...props }: HeadlessFieldProps) {
  return (
    <HeadlessField
      className={clsx(
        className,
        '[&>[data-slot=label]+[data-slot=control]]:mt-3',
        '[&>[data-slot=label]+[data-slot=description]]:mt-1',
        '[&>[data-slot=description]+[data-slot=control]]:mt-3',
        '[&>[data-slot=control]+[data-slot=description]]:mt-3',
        '[&>[data-slot=control]+[data-slot=error]]:mt-3',
        '[&>[data-slot=label]]:font-medium'
      )}
      {...props}
    />
  );
}

export function Label({ className, ...props }: { className?: string } & HeadlessLabelProps) {
  return (
    <HeadlessLabel
      {...props}
      data-slot="label"
      className={clsx(
        className,
        'select-none text-base/6 text-zinc-950 data-[disabled]:opacity-50 sm:text-sm/6 dark:text-white'
      )}
    />
  );
}

export function Description({
  className,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  disabled,
  ...props
}: { className?: string; disabled?: boolean } & HeadlessDescriptionProps) {
  return (
    <HeadlessDescription
      {...props}
      data-slot="description"
      className={clsx(
        className,
        'text-base/6 text-zinc-500 data-[disabled]:opacity-50 sm:text-sm/6 dark:text-zinc-400'
      )}
    />
  );
}

export function ErrorMessage({
  className,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  disabled,
  ...props
}: { className?: string; disabled?: boolean } & HeadlessDescriptionProps) {
  return (
    <HeadlessDescription
      {...props}
      data-slot="error"
      className={clsx(
        className,
        'text-base/6 text-red-600 data-[disabled]:opacity-50 sm:text-sm/6 dark:text-red-500'
      )}
    />
  );
}
