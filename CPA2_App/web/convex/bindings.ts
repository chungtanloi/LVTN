// Schema-bound builders keep backend checks typed before the first cloud codegen.
import {
  queryGeneric,
  mutationGeneric,
  actionGeneric,
  internalQueryGeneric,
  internalMutationGeneric,
  internalActionGeneric,
  type DataModelFromSchemaDefinition,
  type QueryBuilder,
  type MutationBuilder,
  type ActionBuilder,
} from "convex/server";
import schema from "./schema";
type DataModel = DataModelFromSchemaDefinition<typeof schema>;
export const query: QueryBuilder<DataModel, "public"> = queryGeneric;
export const mutation: MutationBuilder<DataModel, "public"> = mutationGeneric;
export const action: ActionBuilder<DataModel, "public"> = actionGeneric;
export const internalQuery: QueryBuilder<DataModel, "internal"> =
  internalQueryGeneric;
export const internalMutation: MutationBuilder<DataModel, "internal"> =
  internalMutationGeneric;
export const internalAction: ActionBuilder<DataModel, "internal"> =
  internalActionGeneric;
