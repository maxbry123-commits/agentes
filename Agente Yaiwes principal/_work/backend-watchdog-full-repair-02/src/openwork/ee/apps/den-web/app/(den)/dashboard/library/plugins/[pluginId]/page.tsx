import { PluginDetailScreen } from "../../../_components/plugin-detail-screen";
import { getLibraryRoute } from "../../../../_lib/den-org";

export default async function LibraryPluginPage({
  params,
}: {
  params: Promise<{ pluginId: string }>;
}) {
  const { pluginId } = await params;

  return <PluginDetailScreen pluginId={pluginId} backHref={getLibraryRoute()} />;
}
