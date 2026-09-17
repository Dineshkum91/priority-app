import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class PriorityScreen extends StatefulWidget {
  final Recommendation recommendation;
  final VoidCallback onRefresh;

  const PriorityScreen({Key? key, required this.recommendation, required this.onRefresh}) : super(key: key);

  @override
  _PriorityScreenState createState() => _PriorityScreenState();
}

class _PriorityScreenState extends State<PriorityScreen> {
  bool _completing = false;

  Future<void> _markComplete() async {
    setState(() => _completing = true);
    await apiService.markComplete(widget.recommendation.id);
    setState(() => _completing = false);
    widget.onRefresh();
  }

  @override
  Widget build(BuildContext context) {
    final rec = widget.recommendation;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 32),
              Text(
                'Today\'s Priority',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.black54),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                rec.priorityDimension.toUpperCase(),
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                  letterSpacing: 2,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
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
                  rec.llmExplanation ?? rec.priorityReason,
                  style: const TextStyle(fontSize: 18, height: 1.5),
                ),
              ),
              const Spacer(),
              if (rec.isCompleted)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.check_circle, color: Colors.green),
                      SizedBox(width: 8),
                      Text('Great job today!', style: TextStyle(color: Colors.green, fontSize: 18, fontWeight: FontWeight.bold)),
                    ],
                  ),
                )
              else
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Colors.white,
                  ),
                  onPressed: _completing ? null : _markComplete,
                  child: _completing 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Mark as Done', style: TextStyle(fontSize: 18)),
                ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
