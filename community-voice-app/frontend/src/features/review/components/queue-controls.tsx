import { FilterSelect } from "@/components/shared/filter-select";
import {
  ALL,
  SORT_OPTIONS,
  type QueueSort,
  type QueueView,
} from "@/features/review/queue-view";
import { humanize } from "@/lib/format";
import { CATEGORIES, URGENCIES } from "@/schemas/domain";

const withAll = (values: readonly string[]) => [
  { value: ALL, label: "All" },
  ...values.map((value) => ({ value, label: humanize(value) })),
];

/** Sort and filter the review queue. */
export const QueueControls = ({
  view,
  statuses,
  onChange,
}: {
  view: QueueView;
  statuses: string[]; // the statuses that are in the queue right now
  onChange: (view: QueueView) => void;
}) => {
  return (
    <div className="grid grid-cols-2 gap-3" role="group" aria-label="Sort and filter">
      <FilterSelect
        id="queue-sort"
        label="Sort"
        value={view.sort}
        options={SORT_OPTIONS}
        onChange={(sort) => onChange({ ...view, sort: sort as QueueSort })}
      />
      <FilterSelect
        id="queue-urgency"
        label="Urgency"
        value={view.urgency}
        options={withAll(URGENCIES)}
        onChange={(urgency) => onChange({ ...view, urgency })}
      />
      <FilterSelect
        id="queue-category"
        label="Category"
        value={view.category}
        options={withAll(CATEGORIES)}
        onChange={(category) => onChange({ ...view, category })}
      />
      <FilterSelect
        id="queue-status"
        label="Status"
        value={view.status}
        options={withAll(statuses)}
        onChange={(status) => onChange({ ...view, status })}
      />
    </div>
  );
};
