import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  getMultimodalSettings,
  updateMultimodalSettings,
  type MultimodalSettings,
} from '@/api/client'
import { queryKeys } from './keys'

export function useMultimodalSettingsQuery() {
  return useQuery({
    queryKey: queryKeys.settings.multimodal(),
    queryFn: getMultimodalSettings,
  })
}

export function useUpdateMultimodalSettingsMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: MultimodalSettings) => updateMultimodalSettings(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings.multimodal() })
    },
  })
}
