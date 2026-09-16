import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import 'checkin_screen.dart';
import 'priority_screen.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({Key? key}) : super(key: key);

  @override
  _TodayScreenState createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  bool _isLoading = true;
  bool _hasCheckedIn = false;
  Recommendation? _recommendation;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final data = await apiService.getTodayHealth();
    setState(() {
      _hasCheckedIn = data['has_checked_in'] ?? false;
      if (data['recommendation'] != null) {
        _recommendation = Recommendation.fromJson(data['recommendation']);
      }
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (_hasCheckedIn && _recommendation != null) {
      return PriorityScreen(recommendation: _recommendation!, onRefresh: _loadData);
    }

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Good Morning',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              const Text(
                'Ready to find your focus for today?',
                style: TextStyle(fontSize: 18, color: Colors.black54),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: () async {
                  await Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const CheckInScreen()),
                  );
                  _loadData(); // Reload after check-in
                },
                child: const Text('Start Daily Check-in', style: TextStyle(fontSize: 18)),
              ),
              const SizedBox(height: 16),
              const Text(
                'Takes less than 30 seconds.',
                style: TextStyle(fontSize: 14, color: Colors.black38),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
