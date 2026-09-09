import React, { useState } from 'react';
import { Link } from 'wouter';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { Intervention, InterventionType } from '../types/api';
import {
  MapPin,
  Search,
  Filter,
  Plus,
  ArrowRight,
  ShieldCheck,
  Calendar,
  X,
  CheckCircle2,
} from 'lucide-react';

export const InterventionsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New intervention form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'farm_pond' as InterventionType,
    latitude: 20.7002,
    longitude: 77.0082,
    village: 'Akhatwada',
    district: 'Akola',
    state: 'Maharashtra',
    implementation_date: '2023-01-15',
    status: 'active' as const,
    description: 'Government funded watershed structure under soil & water conservation cell.',
  });

  // Fetch all interventions for district list
  const { data: allData } = useQuery({
    queryKey: ['interventions-all-districts'],
    queryFn: () => apiClient.listInterventions({ limit: 400 }),
  });
  const allList = allData?.items || [];
  const uniqueDistricts = React.useMemo(() => {
    const set = new Set<string>();
    allList.forEach((it) => {
      if (it.district) set.add(it.district);
    });
    return Array.from(set).sort();
  }, [allList]);

  const { data, isLoading } = useQuery({
    queryKey: ['interventions', selectedType, selectedDistrict],
    queryFn: () =>
      apiClient.listInterventions({
        type: selectedType || undefined,
        district: selectedDistrict || undefined,
        limit: 350,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (newIntervention: Partial<Intervention>) =>
      apiClient.createIntervention(newIntervention),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      setIsModalOpen(false);
    },
  });

  const interventions = data?.items || [];

  const filteredInterventions = interventions.filter((item) => {
    const matchSearch =
      search === '' ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.village.toLowerCase().includes(search.toLowerCase()) ||
      item.district.toLowerCase().includes(search.toLowerCase());
    return matchSearch;
  });

  const handleSubmitNew = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto transition-colors duration-200">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Institutional Registry
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Watershed Interventions Catalog
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Directory of registered farm ponds, check dams, and conservation structures across Maharashtra ({interventions.length} sites).
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center space-x-2 text-xs font-bold bg-emerald-700 hover:bg-emerald-800 text-white px-3.5 py-2 rounded shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Intervention</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by name, village, or district..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded focus:ring-1 focus:ring-emerald-600 focus:outline-none"
          />
        </div>

        <div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full py-2 px-3 border border-slate-200 dark:border-slate-700 rounded focus:ring-1 focus:ring-emerald-600 focus:outline-none bg-slate-50 dark:bg-slate-800 font-medium text-slate-700 dark:text-slate-200"
          >
            <option value="">All Intervention Types</option>
            <option value="farm_pond">Farm Pond</option>
            <option value="check_dam">Check Dam</option>
            <option value="gully_plug">Gully Plug</option>
            <option value="contour_bund">Contour Bund</option>
            <option value="percolation_tank">Percolation Tank</option>
          </select>
        </div>

        <div>
          <select
            value={selectedDistrict}
            onChange={(e) => setSelectedDistrict(e.target.value)}
            className="w-full py-2 px-3 border border-slate-200 dark:border-slate-700 rounded focus:ring-1 focus:ring-emerald-600 focus:outline-none bg-slate-50 dark:bg-slate-800 font-medium text-slate-700 dark:text-slate-200"
          >
            <option value="">All Districts ({allList.length || interventions.length})</option>
            {uniqueDistricts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Interventions Table */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs">
          <span className="font-bold text-slate-700 dark:text-slate-200">
            Registered Interventions ({filteredInterventions.length})
          </span>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            Every site linked to verified bi-temporal satellite photographs & ML change mask
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 text-[11px]">
              <tr>
                <th className="py-3 px-4 font-semibold">Site / Pair</th>
                <th className="py-3 px-4 font-semibold">Intervention Details</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">Location</th>
                <th className="py-3 px-4 font-semibold">Coordinates</th>
                <th className="py-3 px-4 font-semibold">Timeline</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredInterventions.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-10 h-10 rounded overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 flex-shrink-0 relative">
                        <img
                          src={item.t0_url || `/api/preset-image/${item.pair_key || 'Akola_Akhatwada_0'}/t0`}
                          alt="Thumbnail"
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                      <div>
                        <div className="font-mono font-bold text-slate-700 dark:text-slate-200 text-xs">
                          {item.id}
                        </div>
                        {item.pair_key && (
                          <div className="text-[10px] font-mono text-purple-600 dark:text-purple-400 font-semibold">
                            {item.pair_key}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900 dark:text-white">
                      {item.name}
                    </div>
                    {item.change_class && (
                      <span className="inline-block mt-0.5 text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {item.change_class}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-50 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                      {item.type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-slate-300">
                    {item.village}, {item.district}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-500 dark:text-slate-400 text-[11px]">
                    {item.latitude ? `${item.latitude.toFixed(4)}° N, ${item.longitude?.toFixed(4)}° E` : 'Pending GPS'}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-300">
                    <div>{item.implementation_date || '2012-05'}</div>
                    {item.t0_date && item.t1_date && (
                      <div className="text-[10px] text-slate-400 dark:text-slate-500">
                        {item.t0_date} → {item.t1_date}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center space-x-1 text-emerald-700 dark:text-emerald-400 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>{item.status}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link href={`/interventions/${item.id}`}>
                      <a className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-700 dark:text-emerald-300 hover:text-emerald-800 dark:hover:text-emerald-200 bg-emerald-50 dark:bg-emerald-950/80 hover:bg-emerald-100 dark:hover:bg-emerald-900 px-2.5 py-1 rounded transition-colors border border-emerald-200 dark:border-emerald-800">
                        <span>Inspect</span>
                        <ArrowRight className="w-3 h-3" />
                      </a>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Registration Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 max-w-lg w-full p-6 shadow-xl space-y-4 text-slate-900 dark:text-slate-100 transition-colors duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Register New Watershed Intervention</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitNew} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Intervention Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Farm Pond - Akhatwada 10"
                  className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Intervention Type</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  >
                    <option value="farm_pond">Farm Pond</option>
                    <option value="check_dam">Check Dam</option>
                    <option value="gully_plug">Gully Plug</option>
                    <option value="contour_bund">Contour Bund</option>
                    <option value="percolation_tank">Percolation Tank</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Implementation Date</label>
                  <input
                    type="date"
                    value={formData.implementation_date}
                    onChange={(e) => setFormData({ ...formData, implementation_date: e.target.value })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  >
                  </input>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Latitude (°N)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded font-mono bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Longitude (°E)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded font-mono bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Village</label>
                  <input
                    type="text"
                    value={formData.village}
                    onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">District</label>
                  <input
                    type="text"
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    className="w-full p-2 border border-slate-200 dark:border-slate-700 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-1.5 rounded bg-emerald-700 text-white font-bold hover:bg-emerald-800 active:bg-emerald-900"
                >
                  {createMutation.isPending ? 'Saving...' : 'Register Structure'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
