import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CheckInScreen extends StatefulWidget {
  const CheckInScreen({Key? key}) : super(key: key);

  @override
  _CheckInScreenState createState() => _CheckInScreenState();
}

class _CheckInScreenState extends State<CheckInScreen> {
  double _sleepHours = 7.0;
  int _stressLevel = 3;
  int _mealsEaten = 3;
  int _waterGlasses = 4;
  bool _isLoading = false;

  Future<void> _submit() async {
    setState(() => _isLoading = true);
    final data = {
      'check_in_date': DateTime.now().toIso8601String().split('T')[0],
      'sleep_hours': _sleepHours,
      'stress_level': _stressLevel,
      'meals_eaten': _mealsEaten,
      'water_glasses': _waterGlasses,
    };
    await apiService.submitCheckIn(data);
    setState(() => _isLoading = false);
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Daily Check-in')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('How much did you sleep?', style: TextStyle(fontSize: 16)),
            Slider(
              value: _sleepHours,
              min: 0,
              max: 12,
              divisions: 24,
              label: '${_sleepHours.toStringAsFixed(1)} hrs',
              onChanged: (val) => setState(() => _sleepHours = val),
            ),
            const SizedBox(height: 24),
            const Text('Stress level (1-5)?', style: TextStyle(fontSize: 16)),
            Slider(
              value: _stressLevel.toDouble(),
              min: 1,
              max: 5,
              divisions: 4,
              label: _stressLevel.toString(),
              onChanged: (val) => setState(() => _stressLevel = val.toInt()),
            ),
            const SizedBox(height: 24),
            const Text('Meals eaten?', style: TextStyle(fontSize: 16)),
            Slider(
              value: _mealsEaten.toDouble(),
              min: 0,
              max: 5,
              divisions: 5,
              label: _mealsEaten.toString(),
              onChanged: (val) => setState(() => _mealsEaten = val.toInt()),
            ),
            const SizedBox(height: 24),
            const Text('Glasses of water?', style: TextStyle(fontSize: 16)),
            Slider(
              value: _waterGlasses.toDouble(),
              min: 0,
              max: 10,
              divisions: 10,
              label: _waterGlasses.toString(),
              onChanged: (val) => setState(() => _waterGlasses = val.toInt()),
            ),
            const SizedBox(height: 48),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Colors.white,
              ),
              onPressed: _isLoading ? null : _submit,
              child: _isLoading 
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Submit', style: TextStyle(fontSize: 18)),
            ),
          ],
        ),
      ),
    );
  }
}
