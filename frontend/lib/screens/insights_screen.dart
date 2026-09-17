import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({Key? key}) : super(key: key);

  @override
  _InsightsScreenState createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  bool _isLoading = true;
  bool _hasSufficientData = false;
  String _message = '';
  StreakData? _streaks;
  TrendsData? _trends;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      apiService.getWeeklyInsights(),
      apiService.getStreaks(),
      apiService.getTrends(),
    ]);
    if (!mounted) return;
    setState(() {
      final data = results[0] as Map<String, dynamic>;
      _hasSufficientData = data['has_sufficient_data'] ?? false;
      _message = data['message'] ?? 'Unable to load insights.';
      _streaks = results[1] as StreakData?;
      _trends = results[2] as TrendsData?;
      _isLoading = false;
    });
  }

  static const _trendIcons = {
    'improving': Icons.trending_up,
    'declining': Icons.trending_down,
    'stable': Icons.trending_flat,
    'no_data': Icons.remove,
  };

  static const _trendColors = {
    'improving': Colors.green,
    'declining': Colors.red,
    'stable': Colors.grey,
    'no_data': Colors.grey,
  };

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Weekly Insights'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            tooltip: 'Export check-ins as CSV',
            onPressed: () async {
              final csv = await apiService.exportCheckinsCsv();
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(csv != null
                    ? 'CSV ready (${csv.length} bytes) — sharing coming soon'
                    : 'Export failed'),
              ));
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: ListView(
            padding: const EdgeInsets.all(24.0),
            children: [
              // Streak card
              if (_streaks != null) ...[
                Card(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Row(
                      children: [
                        Text(
                          _streaks!.currentStreak >= 7 ? '🔥' : _streaks!.currentStreak >= 3 ? '✨' : '🌱',
                          style: const TextStyle(fontSize: 32),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${_streaks!.currentStreak}-day check-in streak',
                                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _streaks!.message,
                                style: const TextStyle(fontSize: 13, color: Colors.black54),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Weekly insight card
              Icon(
                _hasSufficientData ? Icons.insights : Icons.hourglass_empty,
                size: 64,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                _hasSufficientData ? 'Your Weekly Pattern' : 'Keep Going!',
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4)),
                  ],
                ),
                child: Text(
                  _message,
                  style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.black87),
                  textAlign: TextAlign.center,
                ),
              ),

              // Trend arrows per dimension
              if (_trends != null && _trends!.trends.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Text(
                  'This Week vs Last Week',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                Card(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: _trends!.trends.map((t) {
                      final icon = _trendIcons[t.direction] ?? Icons.remove;
                      final color = _trendColors[t.direction] ?? Colors.grey;
                      return ListTile(
                        leading: Icon(icon, color: color),
                        title: Text(
                          t.dimension.replaceAll('_', ' ').toUpperCase(),
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, letterSpacing: 1),
                        ),
                        subtitle: Text(
                          t.thisWeekAvg != null
                              ? 'This week: ${t.thisWeekAvg!.toStringAsFixed(1)}'
                              : 'No data',
                          style: const TextStyle(fontSize: 12),
                        ),
                        trailing: Text(
                          t.direction == 'no_data' ? '—' : t.direction,
                          style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
