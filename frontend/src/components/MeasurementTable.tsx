import React, { useState } from 'react';
import { Check, CheckCircle2, Ruler, AlertCircle } from 'lucide-react';
import { SizeChartData, MeasurementValues } from '../types/measurements';

interface MeasurementTableProps {
  chartData: SizeChartData;
  selectedSize: string;
  onSizeSelected: (size: string) => void;
  onMeasurementsUpdated: (updatedData: SizeChartData) => void;
  onConfirmMeasurements: () => void;
  isConfirmed: boolean;
}

export const MeasurementTable: React.FC<MeasurementTableProps> = ({
  chartData,
  selectedSize,
  onSizeSelected,
  onMeasurementsUpdated,
  onConfirmMeasurements,
  isConfirmed,
}) => {
  // Ensure canonical sizes S, M, L, XL, XXL in correct order
  const standardSizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const availableChartSizes = Object.keys(chartData.sizes);
  const displaySizes = standardSizes.filter((s) => availableChartSizes.includes(s));
  const sizes = displaySizes.length > 0 ? displaySizes : availableChartSizes;

  const [unit, setUnit] = useState<string>(chartData.unit || 'cm');

  // ONLY 4 ESSENTIAL REQUIRED MEASUREMENTS
  const essentialMeasurementRows: { key: keyof MeasurementValues; label: string; required: boolean }[] = [
    { key: 'chest', label: 'Chest Circumference', required: true },
    { key: 'shoulder', label: 'Shoulder Width', required: true },
    { key: 'length', label: 'Body Length', required: true },
    { key: 'sleeve', label: 'Sleeve Length', required: true },
  ];

  const handleCellChange = (size: string, field: keyof MeasurementValues, valueStr: string) => {
    const val = parseFloat(valueStr);
    const newSizes = { ...chartData.sizes };
    if (!newSizes[size]) return;

    newSizes[size] = {
      ...newSizes[size],
      [field]: isNaN(val) ? 0 : val,
    };

    onMeasurementsUpdated({
      ...chartData,
      sizes: newSizes,
    });
  };

  const handleUnitToggle = (newUnit: string) => {
    if (newUnit === unit) return;
    setUnit(newUnit);

    const factor = newUnit === 'inch' ? 1 / 2.54 : 2.54;
    const newSizes: Record<string, MeasurementValues> = {};

    Object.entries(chartData.sizes).forEach(([sz, vals]) => {
      newSizes[sz] = {
        chest: Math.round(vals.chest * factor * 10) / 10,
        shoulder: Math.round(vals.shoulder * factor * 10) / 10,
        length: Math.round(vals.length * factor * 10) / 10,
        sleeve: vals.sleeve ? Math.round(vals.sleeve * factor * 10) / 10 : null,
        waist: vals.waist ? Math.round(vals.waist * factor * 10) / 10 : null,
        hem: vals.hem ? Math.round(vals.hem * factor * 10) / 10 : null,
        neck: vals.neck ? Math.round(vals.neck * factor * 10) / 10 : null,
        sleeve_opening: vals.sleeve_opening ? Math.round(vals.sleeve_opening * factor * 10) / 10 : null,
      };
    });

    onMeasurementsUpdated({
      ...chartData,
      unit: newUnit,
      sizes: newSizes,
    });
  };

  // Check if active size has any invalid or missing required measurements
  const activeVals = chartData.sizes[selectedSize];
  const hasInvalidRequired =
    !activeVals ||
    !activeVals.chest ||
    activeVals.chest <= 0 ||
    !activeVals.shoulder ||
    activeVals.shoulder <= 0 ||
    !activeVals.length ||
    activeVals.length <= 0 ||
    !activeVals.sleeve ||
    activeVals.sleeve <= 0;

  return (
    <div className="space-y-3 pt-2 border-t studio-border">
      {/* Header & Unit Switcher */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Ruler className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-studio-200">
            Measurements Table
          </h3>
        </div>

        {/* Unit Toggle */}
        <div className="flex items-center bg-studio-900 border border-studio-750 rounded p-0.5 text-[11px] font-mono">
          <button
            onClick={() => handleUnitToggle('cm')}
            className={`px-2 py-0.5 rounded transition-colors ${
              unit === 'cm' ? 'bg-blue-600 text-white font-bold' : 'text-studio-400 hover:text-studio-200'
            }`}
          >
            CM
          </button>
          <button
            onClick={() => handleUnitToggle('inch')}
            className={`px-2 py-0.5 rounded transition-colors ${
              unit === 'inch' ? 'bg-blue-600 text-white font-bold' : 'text-studio-400 hover:text-studio-200'
            }`}
          >
            INCH
          </button>
        </div>
      </div>

      {/* Editable Table */}
      <div className="border border-studio-800 rounded-lg overflow-x-auto bg-studio-950/60 max-w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-studio-800 bg-studio-900/80 text-[11px] font-mono text-studio-400">
              <th className="p-2 pl-3 font-semibold text-studio-300">Measurement</th>
              {sizes.map((sz) => {
                const isSelected = sz === selectedSize;
                return (
                  <th
                    key={sz}
                    onClick={() => onSizeSelected(sz)}
                    className={`p-2 text-center cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-600/20 text-blue-400 font-bold border-b-2 border-blue-500'
                        : 'hover:bg-studio-800/60 text-studio-300'
                    }`}
                  >
                    <span>{sz}</span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-studio-850">
            {essentialMeasurementRows.map((row) => (
              <tr key={row.key} className="hover:bg-studio-900/40 transition-colors">
                <td className="p-2 pl-3 text-studio-300 font-medium whitespace-nowrap">
                  <div className="flex items-center space-x-1.5">
                    <span>{row.label}</span>
                    <span className="text-blue-400 font-bold text-[10px]">*</span>
                  </div>
                </td>
                {sizes.map((sz) => {
                  const isSelected = sz === selectedSize;
                  const rawVal = chartData.sizes[sz]?.[row.key];
                  const val = typeof rawVal === 'number' ? rawVal : null;
                  const conf = chartData.cell_confidences?.[sz]?.[row.key];
                  const isLowConf = conf !== undefined && conf < 0.75;
                  const isZeroOrMissing = val === null || val <= 0;

                  return (
                    <td
                      key={sz}
                      className={`p-1.5 text-center transition-colors ${
                        isSelected ? 'bg-blue-600/10 font-semibold' : ''
                      }`}
                    >
                      <div className="relative flex items-center justify-center">
                        <input
                          type="number"
                          step="0.5"
                          value={val !== null && val > 0 ? val : ''}
                          placeholder="-"
                          onChange={(e) => handleCellChange(sz, row.key, e.target.value)}
                          className={`w-14 text-center font-mono py-1 rounded border text-xs focus:outline-none transition-all ${
                            isZeroOrMissing
                              ? 'bg-rose-950/40 text-rose-300 border-rose-500/60 focus:border-rose-400'
                              : isSelected
                              ? 'bg-studio-900 text-blue-300 border-blue-500/50 focus:border-blue-400 focus:ring-1 focus:ring-blue-400'
                              : 'bg-studio-900/50 text-studio-200 border-studio-800 hover:border-studio-700 focus:border-studio-600'
                          }`}
                        />
                        {isLowConf && !isZeroOrMissing && (
                          <span
                            title="Low OCR confidence - please verify"
                            className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-amber-400 ring-2 ring-studio-950"
                          />
                        )}
                        {isZeroOrMissing && (
                          <span
                            title="Required measurement missing or 0"
                            className="absolute -top-1 -right-1 flex items-center justify-center"
                          >
                            <AlertCircle className="w-3 h-3 text-rose-400" />
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Validation Warning if active size has 0 or missing values */}
      {hasInvalidRequired && (
        <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Size <strong className="font-bold text-white">{selectedSize}</strong> has missing or zero required measurements. Please correct them in the table before generating.
          </span>
        </div>
      )}

      {/* Selected Size Highlight & Confirm Button */}
      <div className="p-3 rounded-lg bg-studio-900 border border-studio-800 flex items-center justify-between text-xs">
        <div>
          <span className="text-studio-400">Selected Size: </span>
          <span className="font-bold text-white text-sm ml-1 px-1.5 py-0.5 rounded bg-blue-600/30 text-blue-300 border border-blue-500/30">
            {selectedSize}
          </span>
          <div className="text-[11px] font-mono text-studio-400 mt-1">
            Chest: {chartData.sizes[selectedSize]?.chest || '-'} {unit} • Length: {chartData.sizes[selectedSize]?.length || '-'} {unit}
          </div>
        </div>

        {/* Confirm Button */}
        <button
          onClick={onConfirmMeasurements}
          disabled={hasInvalidRequired}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            hasInvalidRequired
              ? 'bg-studio-800 text-studio-500 border border-studio-700 cursor-not-allowed'
              : isConfirmed
              ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 shadow-sm'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/30 active:scale-[0.99]'
          }`}
        >
          {isConfirmed && !hasInvalidRequired ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Confirmed</span>
            </>
          ) : (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Confirm Measurements</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
